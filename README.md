# Iconix: Discord Skins for Vesktop v2.0.0

Makes Vesktop feel more at home for the average Discord enjoyers.


1. Download [this repository](https://github.com/Arcitec/iconix).

2. Install the Python3 requirements:

```sh
pip install -r requirements.txt
```

3. (Optional) Install CairoSVG if you want to build icons from SVG files. You may also need to install some [external packages](https://cairosvg.org/documentation/) to use CairoSVG.

```sh
pip install -r requirements-svg.txt
```

4. Run the patcher and follow the instructions. If you decide to use custom icons, remember that their contents should extend to the edges of the input image (without any padding).

```sh
./iconix.py
```

5. Have fun! You *never* have to run the patcher again.


---

### Custom Icons

Here are some useful resources for Discord SVG and PNG icons. You should sign up and use their online editors to ensure that you crop the icon very close to the square edges before downloading, for the best visual results as an icon. Their editors will also allow you to choose your own, custom colors to personalize your icons.

If the website allows you to download icons as PNG with a custom resolution of 1024x1024, then you should prefer that instead of SVGs, since the CairoSVG renderer isn't perfect and it's therefore preferable to use large PNG files.

- [IconScout.com](https://iconscout.com/icons/discord?price=free): The largest collection with the most variation and unique icons. This site lets you download as 1024x1024 PNGs. It has an incredibly good icon editor for custom colors and styles. Try their "Palettes" feature for quick and beautiful style changes, which you can then tweak further via the regular color picker afterwards. You can even click directly on a part of an icon to recolor that specific part.
- [Icons8.com](https://icons8.com/icons/set/discord): Good collection with several very nice icons. Most icons here need negative padding in their editor to remove the empty borders.
- [SvgRepo.com](https://www.svgrepo.com/vectors/discord/): Pretty decent icons, but they are all flat-shaded. They could be useful for someone who wants to import them in Inkscape and design their own gradients, though.
- [My personal favorite icon](https://iconscout.com/free-icon/discord-11306594): It's a really fresh and unique "rounded diamond" shape, with great recoloring options and a beautiful gradient design. There are also [round](https://iconscout.com/free-icon/discord-11306407) and [square](https://iconscout.com/free-icon/discord-11306355) variants. They are designed by "[Motion Fans - Creative Studio](https://iconscout.com/contributors/seba086)".
- My color presets for my favorite icon: [Diamond](https://iconscout.com/svg-editor?state=XQAAAALqAAAAAAAAAABt__348v1FAx8N3lMcQCONOyOsOielAEk-g5Qn3gAnEv5AkFUsKBoMEi0VXghrWo0E277rAMCN8VTVZyEsWoHYBmODlDPJ1cU7Zmu-eCAqjUhieFjIsjnWz_jym6BoH10nXUgzdnnYXQVQJoCrz-2lYCormX9oUwVzVTvKUkz_g8voTAvPbqg1Ggz0_ZsfxLzosFyuKKtv8HVhocC1GXdlBTqGIUmq9rbp173LzNmDSqfMog2K43pWUmi0XAmYyKm7kKY1rc3vWQ-7HxoL2Wlae3vCRjmTQe6u9__4ElsA), [Circle](https://iconscout.com/svg-editor?state=XQAAAALqAAAAAAAAAABt__348v1FAx8N3lMcQCOdcX6Dft1T1Q0lLuZxwW1a7J3PQkhVpH91Ki2AUgv8v61qyVFPXVNEsVfPUuX79LF8Mtfi7vJ2EOTulAi7LrJqJk7DXp84GhBIKDzoGzEF0RGV-ZG0IkyNWa5jEM5KF1Pb0PD5vj73_GHq58BHsE5YcQxFlEtJnJlXxzOWjkys1eBVguGUtvlrGtN34ba6qnQ19E-zQF5nI2PIKInYBMWVGLU-cebkdIPjTrdt6vMlxQPyV0TfWYSOONGcF5NxslqBUYqCeaiKHuj_xhRAAA) and [Square](https://iconscout.com/svg-editor?state=XQAAAALqAAAAAAAAAABt__348v1FAx8N3lMcQCONOyOsOielAEk-g5Qn3gAnEv5AkFUsKBoMEi0VXghrWo0E277rAMCN8VTVZyEsWoHYBmODlDPJ1cU7Zmu-eCAqjUhieFjIsjnWz_jym6BoH10nXUgzdnnYXQVQJoCrz-2lYCormX9oSUYraBnHl5DDWqoBVB6LXoh7CVfruDVUtjXzFLr98P8YWkWl6__FanyDRbJZ_BefqLf7T_lFKRVFltwtozL0egCmMSuk1k96U3uC7w_Zy6ENKd7l0DKHzeDaynoCQHYrcapXmf_Jk9AA). Download these as 1024x1024 PNGs for the best rendering results. They are also included in this repository, in the **icon_packs/motion_fans/** directory.


---

### Legal Notice

*This project does not contain any artwork from Discord.*

*Discord is a registered trademark of Discord Inc.*
