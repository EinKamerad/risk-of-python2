from ursina import *
from config import ctx, rgb
from ui import GameManager

app = Ursina(
    title='Risk of Python 2 - LAN & Room Code Co-Op',
    borderless=False,
    size=(1536, 864)
)

window.color = rgb(18, 20, 32)
scene.fog_color = rgb(18, 20, 32)
scene.fog_density = 0.011

game = GameManager()


def input(key):
    if not ctx.game.running:
        # Если активно поле ввода кода комнаты, передаём нажатия туда
        if ctx.game.handle_menu_key(key):
            return
        if key == '1':
            ctx.game.start_run('commando')
        elif key == '2':
            ctx.game.start_run('artificer')
        elif key == '3':
            ctx.game.start_run('huntress')
    elif key == 'escape':
        mouse.locked = not mouse.locked


if __name__ == '__main__':
    app.run()