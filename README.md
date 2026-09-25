# Cupcake Collector

Cupcake Collector is a simple Pygame platform game. Move the chicken across randomized short mint-colored platforms, use a double jump, and collect all ten cupcakes before the 60-second timer runs out.

## Run in a Browser

The game uses an async game loop so it can be packaged for the browser with Pygbag.

```bash
python -m pip install -r requirements.txt
python -m pygbag --build main.py
```

Open the local address shown by Pygbag. The generated browser files are placed in `build/web`.

## Controls

- **A / D** or **Left / Right arrows**: Move
- **Space**, **W**, or **Up arrow**: Jump or double jump
- **R**: Restart the game
- **Space** on the win or lose screen: Play again

The top-left display shows how many cupcakes remain and how much time is left. Collect every cupcake to win. If the timer reaches zero, you lose. Both screens let you press Space to play again with a new randomized layout.

The game uses the custom chicken and cupcake sprites in the `assets` folder. Add an image named `assets/background.png` to use a custom background; otherwise, the game creates a matching city-and-sky background automatically.

## GitHub Pages

The repository includes a GitHub Actions workflow in `.github/workflows/pages.yml`. Push the project to GitHub, select **GitHub Actions** as the Pages source in repository settings, and the workflow will build and deploy the browser version.

