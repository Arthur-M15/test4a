from PIL import Image, ImageFilter
import math


"""import numpy as np
import matplotlib.pyplot as plt

def generate_colored_signal(power, B, N, dt=1.0, seed=None):

    Generate a colored signal with uniform Fourier spectrum, centered, and specified power.

    Parameters:
    - power: desired average power of the signal.
    - B: maximum frequency (Hz).
    - N: number of points in the time series.
    - dt: time step (default 1.0).
    - seed: seed for reproducibility (default None).

    Returns:
    - t: time array.
    - x: time-domain signal with specified properties.

    if seed is not None:
        np.random.seed(seed)

    # Frequency array
    freqs = np.fft.rfftfreq(N, dt)

    # Mask to keep frequencies below B
    freq_mask = freqs <= B

    # Generate uniform amplitudes and random phases for frequencies below B
    amplitudes = np.random.uniform(0, 1, size=len(freqs)) * freq_mask
    phases = np.random.uniform(0, 2 * np.pi, size=len(freqs))

    # Construct Fourier coefficients
    fourier_coeffs = amplitudes * np.exp(1j * phases)

    # Inverse Fourier Transform to get time-domain signal
    x = np.fft.irfft(fourier_coeffs, n=N)

    # Center the signal (mean = 0)
    x -= np.mean(x)

    # Normalize to the desired power
    current_power = np.mean(x**2)
    scaling_factor = np.sqrt(power / current_power)
    x *= scaling_factor

    # Time array
    t = np.arange(0, N * dt, dt)

    return t, x

# Parameters
power = 1.0  # Desired average power
B = 0.2        # Maximum frequency (Hz)
N = 2**14    # Number of points
dt = 0.01    # Time step
seed = 42    # Fixed seed for reproducibility

# Generate the signal
t, x = generate_colored_signal(power, B, N, dt, seed)

# Plot the signal
plt.figure(figsize=(10, 4))
plt.plot(t, x, label=f'Signal with B = {B} Hz, Power = {power}')
plt.xlabel('Time')
plt.ylabel('Amplitude')
plt.title('Colored Signal with Uniform Fourier Spectrum')
plt.legend()
plt.grid()
plt.show()

# Compute and plot the Power Spectral Density
freqs = np.fft.rfftfreq(N, dt)
psd = np.abs(np.fft.rfft(x))**2
plt.figure(figsize=(10, 4))
plt.plot(freqs, psd, label='Power Spectral Density')
plt.axvline(B, color='r', linestyle='--', label=f'Cutoff Frequency = {B} Hz')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Power')
plt.title('Power Spectral Density of the Signal')
plt.legend()
plt.grid()
plt.show()
"""