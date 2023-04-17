import struct

import numpy as np
from vispy import scene, color
from vispy.app import Timer
from vispy.util.quaternion import Quaternion

FPS = 25.0
MAX_Z_SIZE = 9100000  # Maximal amount of data in Z we were able to plot

SCALE_FACTOR = 1 / 12200.
Y_STEP = 60  # Figure out how to make this better
Z_FACTOR = 0.033
INNER_PORTION = 4

i = 0


def animate_spectrum(data, nfft, sample_size, z_max):
    # TODO: Use i to know which part of readframes array to read
    number_of_samples = len(data) / sample_size
    # Unpack data, LRLRLR... Down-scale Z
    maximal_sample_value = (2.0 ** (sample_size * 8 - 1))
    unpacked_data = np.array(struct.unpack("%dh" % number_of_samples, data)) / maximal_sample_value
    left_channel = unpacked_data[::2]
    right_channel = unpacked_data[1::2]

    # For real inputs, fft output is symmetric, so we can take only one side
    z_left = np.fft.fft(left_channel, nfft)[-nfft // 2:]
    z_right = np.fft.fft(right_channel, nfft)[1:nfft // 2 + 1]

    z_left = z_left[-len(z_left) // INNER_PORTION:]
    z_right = z_right[:len(z_right) // INNER_PORTION]

    # Sewing FFT of two channels together, DC part uses right channel's
    # We use abs to extract magnitude (Re) value from the complex output of fft (Im value is the phase)
    z_unscaled = abs(np.hstack((z_left, [0, 0], z_right)))

    # Since values in Z can sometimes be quite high and sometimes quite low, we scale them so that the maximal value
    #  is always portrayed as Z_MAX and other values can be deduced by comparing to it
    z_scaled = z_unscaled * z_max
    if np.amax(z_unscaled):
        z_scaled = z_scaled / np.amax(z_unscaled)

    return z_scaled


def compute_spectrum(frames_array, sample_size, rate, num_frames, nfft, mixer_sound, log_input=False):
    # Creates a buffer around the zero so that L and R channel don't seem intertwined
    buffer_size = max(int(0.01 * nfft), 2)
    print('Calculating coordinates...')
    # Frequency range
    x = np.arange(buffer_size - 1, buffer_size + nfft / 2)
    if log_input:
        print('Using logarithmic frequency scale')
        x = np.log(x)
    x = x / nfft * rate / 2
    x = x - (x.min() - 1)
    x_max = (buffer_size + nfft / 2 - 1) / nfft * rate / 2
    x = x * x_max / x.max()  # Scale X to preferred size
    x = x[:len(x) // INNER_PORTION + 1]
    x = np.concatenate([-x[::-1], x])  # Reflect x to the negative side

    y = np.array([Y_STEP * i for i in range(0, num_frames)])

    z_max = np.max(x) * Z_FACTOR
    z = np.array(
        [animate_spectrum(frame, nfft, sample_size, z_max) for frame in frames_array]
    ).transpose()
    print('Coordinates calculated')

    print('Calculating color map...')
    z_colormap = np.divide(
        z, abs(np.amax(z)), out=np.zeros_like(z), where=abs(np.amax(z)) != 0
    )
    c = color.get_colormap("diverging").map(z_colormap).reshape(z.shape + (-1,)).flatten().tolist()
    c = list(map(lambda x, y, z, w: (x, y, z, w), c[0::4], c[1::4], c[2::4], c[3::4]))
    print('Color map calculated')

    print('Initial calculations done, creating objects...')
    plot = scene.visuals.SurfacePlot(x, y, z)
    plot.mesh_data.set_vertex_colors(c)
    plot.transform = scene.transforms.MatrixTransform()
    plot.transform.scale([SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR])

    left_cube = scene.visuals.Box(z_max, 2 * z_max, z_max, color=(1, 0, 0, 1))
    left_cube.transform = scene.transforms.MatrixTransform()
    left_cube.transform.translate([np.min(x) - z_max / 2, 0, 0])
    left_cube.transform.scale([SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR])

    right_cube = scene.visuals.Box(z_max, 2 * z_max, z_max, color=(1, 0, 0, 1))
    right_cube.transform = scene.transforms.MatrixTransform()
    right_cube.transform.translate([np.max(x) + z_max / 2, 0, 0])
    right_cube.transform.scale([SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR])

    black_cube = scene.visuals.Box(2 * np.max(x), 3 * z_max, 2 * Y_STEP * num_frames, color=(0, 0, 0, 1))
    black_cube.transform = scene.transforms.MatrixTransform()
    black_cube.transform.translate([0, Y_STEP * (num_frames + 2), 0])
    black_cube.transform.scale([SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR])

    xax = scene.Axis(
        pos=[[np.min(x) * SCALE_FACTOR, 0], [np.max(x) * SCALE_FACTOR, 0]], domain=(-rate / 2, rate / 2),
        tick_direction=(0, -1), axis_label='Frequencies', font_size=4, axis_color='w', tick_color='w', text_color='w'
    )

    duration = mixer_sound.get_length()
    yax = scene.Axis(
        pos=[[0, 0], [0, Y_STEP * num_frames * SCALE_FACTOR]], axis_label='Time', font_size=4, tick_direction=(-1, 0),
        axis_label_margin=45, axis_color='w', tick_color='w', text_color='w',
        domain=(0, duration)
    )
    zax = scene.Axis(
        pos=[[0, 0], [0, z_max * SCALE_FACTOR]], font_size=4, tick_direction=(1, 0),
        axis_color='w', tick_color='w', text_color='w', domain=(0, z_max)
    )
    zax.transform = scene.transforms.MatrixTransform()
    zax.transform.rotate(90, (1, 0, 0))
    zax_2 = scene.Axis(
        pos=[[0, 0], [0, z_max * SCALE_FACTOR]], axis_label='Amplitude', font_size=4, tick_direction=(1, 0),
        axis_color='w', tick_color='w', text_color='w', domain=(0, z_max)
    )
    zax_2.transform = scene.transforms.MatrixTransform()
    zax_2.transform.rotate(90, (1, 0, 0))
    zax_2.transform.translate((0, Y_STEP * num_frames * SCALE_FACTOR / 2, 0))
    zax_3 = scene.Axis(
        pos=[[0, 0], [0, z_max * SCALE_FACTOR]], axis_label='Amplitude', font_size=4, tick_direction=(1, 0),
        axis_color='w', tick_color='w', text_color='w', domain=(0, z_max)
    )
    zax_3.transform = scene.transforms.MatrixTransform()
    zax_3.transform.rotate(90, (1, 0, 0))
    zax_3.transform.translate((0, Y_STEP * num_frames * SCALE_FACTOR, 0))

    # Add a 3D axis to keep us oriented
    xyz_axis = scene.visuals.XYZAxis()
    print('Objects created')

    print('Creating the scene')
    canvas = scene.SceneCanvas(keys='interactive', fullscreen=True)
    print('Scene created')

    print('Adding objects to the scene')
    view = canvas.central_widget.add_view()
    view.camera = scene.FlyCamera()  # W S A D F C
    view.camera.rotation1 = Quaternion(1, -0.5, 0, 0)
    view.camera.center = (0, -1, 1)
    view.add(plot)
    view.add(black_cube)
    view.add(left_cube)
    view.add(right_cube)
    view.add(xax)
    view.add(yax)
    view.add(zax)
    view.add(zax_2)
    view.add(zax_3)
    view.add(xyz_axis)
    print('Objects added to the scene')

    def move_cubes(_):
        global i
        if i == 0 or i % num_frames != 0:
            right_cube.transform.translate([0, SCALE_FACTOR * Y_STEP, 0])
            left_cube.transform.translate([0, SCALE_FACTOR * Y_STEP, 0])
            black_cube.transform.translate([0, SCALE_FACTOR * Y_STEP, 0])
        else:
            right_cube.transform.translate([0, - num_frames * SCALE_FACTOR * Y_STEP, 0])
            left_cube.transform.translate([0, - num_frames * SCALE_FACTOR * Y_STEP, 0])

        if i == num_frames:
            black_cube.parent = None

        i += 1

    app = canvas.app
    timer = Timer(interval=1. / FPS, connect=move_cubes, iterations=-1, app=app)
    print('Revealing the scene..')
    canvas.show()
    print('Playing the show')
    mixer_sound.play(loops=-1)
    timer.start()
    app.run()
