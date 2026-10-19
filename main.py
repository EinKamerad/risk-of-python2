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
        if ctx.game.handle_menu_key(key):
            return

        # В лобби клавиши 1-9, 0, -, =, [, ] выбирают одного из 14 выживших
        if ctx.game.menu_state == 'lobby':
            key_map = {
                '1': 'commando',
                '2': 'artificer',
                '3': 'huntress',
                '4': 'buzz',
                '5': 'v1',
                '6': 'sol',
                '7': 'gwen',
                '8': 'enforcer',
                '9': 'scout',
                '0': 'm4a1',
                '-': 'medic',
                '=': 'aigis',
                '[': 'reimu',
                ']': 'mindustry'
            }
            if key in key_map:
                ctx.game.select_lobby_character(key_map[key])
            elif key == 'escape':
                ctx.game.leave_lobby_to_main()
        elif ctx.game.menu_state in ('mp_connect', 'settings') and key == 'escape':
            ctx.game.show_screen('main')
    elif key == 'escape':
        mouse.locked = not mouse.locked


if __name__ == '__main__':
    app.run()