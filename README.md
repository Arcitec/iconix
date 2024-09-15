# Iconix: Discord Skins for Vesktop v2.1.0

Makes Vesktop feel more at home for the average Discord enjoyers.


1. Download [this repository](https://github.com/Arcitec/iconix).

2. Ensure that you have Python 3.10 (or preferably even higher) on your system. You can check by running the following command:

```sh
python --version
```

3. (Optional) If your distro ships an ancient Python version, then you will need to install a newer one with [pyenv](https://github.com/pyenv/pyenv), and then tell Iconix to use it, by running the following commands inside the `iconix` directory:

```sh
pyenv install 3.12
pyenv local 3.12
```

4. Install the Python3 requirements:

```sh
python -m pip install -r requirements.txt
```

5. (Optional) Install CairoSVG if you want to build icons from SVG files. You may also need to install some [external packages](https://cairosvg.org/documentation/) to use CairoSVG.

```sh
python -m pip install -r requirements-svg.txt
```

6. Run the patcher and follow the instructions. If you decide to use custom icons, remember that their contents should extend to the edges of the input image (without any padding).

```sh
./iconix
```

7. Have fun! You *never* have to run the patcher again.


---

### Custom Icons

Here are some useful resources for Discord SVG and PNG icons. You should sign up and use their online editors to ensure that you crop the icon very close to the square edges before downloading, for the best visual results as an icon. Their editors will also allow you to choose your own, custom colors to personalize your icons.

If the website allows you to download icons as PNG with a custom resolution of 1024x1024, then you should prefer that instead of SVGs, since the CairoSVG renderer isn't perfect and it's therefore preferable to use large PNG files.

- [IconScout.com](https://iconscout.com/icons/discord?price=free): The largest collection with the most variation and unique icons. This site lets you download as 1024x1024 PNGs. It has an incredibly good icon editor for custom colors and styles. Try their "Palettes" feature for quick and beautiful style changes, which you can then tweak further via the regular color picker afterwards. You can even click directly on a part of an icon to recolor that specific part.
- [Icons8.com](https://icons8.com/icons/set/discord): Good collection with several very nice icons. Most icons here need negative padding in their editor to remove the empty borders.
- [SvgRepo.com](https://www.svgrepo.com/vectors/discord/): Pretty decent icons, but they are all flat-shaded. They could be useful for someone who wants to import them in Inkscape and design their own gradients, though.
- My personal favorite icon: It's a really fresh and unique design, with great recoloring options and beautiful gradients and shadows. There are [round](https://iconscout.com/free-icon/discord-11306407), [square](https://iconscout.com/free-icon/discord-11306355) and [diamond](https://iconscout.com/free-icon/discord-11306594) variants. They are designed by "[Motion Fans - Creative Studio](https://iconscout.com/contributors/seba086)". Download these as 1024x1024 PNGs for the best rendering results.
- **My icon packs:** Explore the **icon_packs/motion_fans/** directory for a great selection of meticulously finetuned colorways, carefully designed to offer you a wide variety of unique and visually striking designs. These were all designed from scratch, with the Motion Fans SVG shapes as their basis.


---

### Legal Notice

*This project does not contain any artwork from Discord.*

*Discord is a registered trademark of Discord Inc.*
