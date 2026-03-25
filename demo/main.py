# main.py - 游戏入口

import tkinter as tk
from game_logic import GameState
from ui import UIComponents


class CardGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("调查员与神话 - Investigator & Mythos")
        self.root.geometry("1100x850")
        self.root.configure(bg='#1a1a2e')
        self.root.resizable(False, False)

        # 初始化游戏状态
        self.game_state = GameState()

        # 初始化UI
        self.ui = UIComponents(self.root, self.game_state)

        # 初始抽牌
        for _ in range(5):
            self.game_state.draw_card()

        # 启动游戏
        self._start_game()

    def _start_game(self):
        self.game_state.log("=== 第一回合开始 ===")
        self.game_state.log("第一个回合，跳过神话阶段")
        self.game_state.start_investigation_phase()
        self.ui.update_display()

    def run(self):
        self.root.mainloop()


def main():
    game = CardGame()
    game.run()


if __name__ == "__main__":
    main()
