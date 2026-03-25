# ui.py - 用户界面

import tkinter as tk
from tkinter import font as tkfont
from constants import COLORS, LOCATIONS, LOCATION_MAP, LOCATION_CONNECTIONS


# ========== UI组件 ==========

class UIComponents:
    def __init__(self, root, game_state):
        self.root = root
        self.game = game_state
        self.game.on_state_change = self._on_state_change

        self.widgets = {}
        self._create_ui()

    def _on_state_change(self, event_type, data):
        if event_type == 'update' or event_type == 'phase' or event_type == 'log':
            self.update_display()

    def _create_ui(self):
        # 标题
        tk.Label(
            self.root, text="调查员与神话",
            font=tkfont.Font(family="Microsoft YaHei", size=24, weight="bold"),
            fg=COLORS['accent'], bg=COLORS['bg']
        ).pack(pady=5)

        # 状态栏
        self._create_status_bar()

        # 章节流程区域
        self._create_scenario_area()

        # 主游戏区域
        self._create_main_area()

        # 手牌区域
        self._create_hand_area()

        # 行动按钮
        self._create_action_buttons()

        # 日志区域
        self._create_log_area()

    def _create_status_bar(self):
        self.widgets['status_bar'] = tk.Frame(self.root, bg=COLORS['panel'], relief=tk.RAISED, bd=2)
        self.widgets['status_bar'].pack(fill=tk.X, padx=10, pady=5)

        self.widgets['turn_label'] = tk.Label(
            self.widgets['status_bar'], text="回合: 1",
            font=tkfont.Font(family="Microsoft YaHei", size=14), fg=COLORS['text'], bg=COLORS['panel']
        )
        self.widgets['turn_label'].pack(side=tk.LEFT, padx=15)

        self.widgets['phase_label'] = tk.Label(
            self.widgets['status_bar'], text="阶段: 调查阶段",
            font=tkfont.Font(family="Microsoft YaHei", size=14, weight="bold"), fg=COLORS['accent'], bg=COLORS['panel']
        )
        self.widgets['phase_label'].pack(side=tk.LEFT, padx=15)

        self.widgets['ap_label'] = tk.Label(
            self.widgets['status_bar'], text="行动点: 3/3",
            font=tkfont.Font(family="Microsoft YaHei", size=14), fg=COLORS['success'], bg=COLORS['panel']
        )
        self.widgets['ap_label'].pack(side=tk.LEFT, padx=15)

        self.widgets['clue_label'] = tk.Label(
            self.widgets['status_bar'], text="线索: 0",
            font=tkfont.Font(family="Microsoft YaHei", size=14), fg=COLORS['clue'], bg=COLORS['panel']
        )
        self.widgets['clue_label'].pack(side=tk.LEFT, padx=15)

    def _create_scenario_area(self):
        scenario_frame = tk.LabelFrame(
            self.root, text=" 章节流程 ",
            font=tkfont.Font(family="Microsoft YaHei", size=12, weight="bold"),
            fg=COLORS['text'], bg=COLORS['panel'], relief=tk.RAISED, bd=2
        )
        scenario_frame.pack(fill=tk.X, padx=10, pady=5)
        self.widgets['scenario_frame'] = scenario_frame

        # 场景卡
        tk.Label(
            scenario_frame, text="【场景卡】",
            font=tkfont.Font(family="Microsoft YaHei", size=11, weight="bold"),
            fg=COLORS['scene'], bg=COLORS['panel']
        ).pack(anchor='w', padx=10, pady=(5, 0))

        self.widgets['scene_cards_frame'] = tk.Frame(scenario_frame, bg=COLORS['panel'])
        self.widgets['scene_cards_frame'].pack(fill=tk.X, padx=10, pady=5)

        # 密谋卡
        tk.Label(
            scenario_frame, text="【密谋卡】",
            font=tkfont.Font(family="Microsoft YaHei", size=11, weight="bold"),
            fg=COLORS['doom'], bg=COLORS['panel']
        ).pack(anchor='w', padx=10, pady=(5, 0))

        self.widgets['mythos_cards_frame'] = tk.Frame(scenario_frame, bg=COLORS['panel'])
        self.widgets['mythos_cards_frame'].pack(fill=tk.X, padx=10, pady=5)

    def _create_main_area(self):
        self.widgets['main_frame'] = tk.Frame(self.root, bg=COLORS['bg'])
        self.widgets['main_frame'].pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 左侧列
        left_column = tk.Frame(self.widgets['main_frame'], bg=COLORS['bg'])
        left_column.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))

        # 玩家状态面板
        player_panel = tk.LabelFrame(
            left_column, text=" 调查员状态 ",
            font=tkfont.Font(family="Microsoft YaHei", size=12, weight="bold"),
            fg=COLORS['text'], bg=COLORS['panel'], relief=tk.RAISED, bd=2
        )
        player_panel.pack(fill=tk.X, pady=(0, 5))
        self.widgets['player_panel'] = player_panel

        # 属性显示
        self.widgets['stats_label'] = tk.Label(
            player_panel, text="力量: 3  速度: 3\n智慧: 4  胆识: 3",
            font=tkfont.Font(family="Microsoft YaHei", size=11),
            fg=COLORS['text'], bg=COLORS['panel'], justify='left'
        )
        self.widgets['stats_label'].pack(anchor='w', padx=10, pady=5)

        # HP条
        hp_frame = tk.Frame(player_panel, bg=COLORS['panel'])
        hp_frame.pack(fill=tk.X, padx=10, pady=2)
        tk.Label(hp_frame, text="HP:", font=tkfont.Font(size=11), fg=COLORS['danger'], bg=COLORS['panel']).pack(side=tk.LEFT)
        self.widgets['hp_bar'] = tk.Canvas(hp_frame, width=100, height=14, bg=COLORS['bg'], highlightthickness=0)
        self.widgets['hp_bar'].pack(side=tk.LEFT, padx=5)
        self.widgets['hp_text'] = tk.Label(hp_frame, text="10/10", font=tkfont.Font(size=10), fg=COLORS['danger'], bg=COLORS['panel'])
        self.widgets['hp_text'].pack(side=tk.LEFT)

        # SAN条
        san_frame = tk.Frame(player_panel, bg=COLORS['panel'])
        san_frame.pack(fill=tk.X, padx=10, pady=2)
        tk.Label(san_frame, text="SAN:", font=tkfont.Font(size=11), fg=COLORS['mythos'], bg=COLORS['panel']).pack(side=tk.LEFT)
        self.widgets['san_bar'] = tk.Canvas(san_frame, width=100, height=14, bg=COLORS['bg'], highlightthickness=0)
        self.widgets['san_bar'].pack(side=tk.LEFT, padx=5)
        self.widgets['san_text'] = tk.Label(san_frame, text="8/8", font=tkfont.Font(size=10), fg=COLORS['mythos'], bg=COLORS['panel'])
        self.widgets['san_text'].pack(side=tk.LEFT)

        # 位置
        self.widgets['loc_label'] = tk.Label(
            player_panel, text="位置: 酒馆",
            font=tkfont.Font(family="Microsoft YaHei", size=11),
            fg=COLORS['location'], bg=COLORS['panel']
        )
        self.widgets['loc_label'].pack(anchor='w', padx=10, pady=5)

        # 牌组面板
        deck_panel = tk.LabelFrame(
            left_column, text=" 牌组 ",
            font=tkfont.Font(family="Microsoft YaHei", size=12, weight="bold"),
            fg=COLORS['text'], bg=COLORS['panel'], relief=tk.RAISED, bd=2
        )
        deck_panel.pack(fill=tk.X, pady=(0, 5))

        self.widgets['deck_label'] = tk.Label(
            deck_panel, text="牌组: 10张",
            font=tkfont.Font(family="Microsoft YaHei", size=11),
            fg=COLORS['scene'], bg=COLORS['panel']
        )
        self.widgets['deck_label'].pack(anchor='w', padx=10, pady=5)

        self.widgets['discard_label'] = tk.Label(
            deck_panel, text="弃牌堆: 0张",
            font=tkfont.Font(family="Microsoft YaHei", size=11),
            fg=COLORS['text_dim'], bg=COLORS['panel']
        )
        self.widgets['discard_label'].pack(anchor='w', padx=10, pady=5)

        tk.Button(
            deck_panel, text="抽牌",
            command=lambda: self.game.draw_card(),
            font=tkfont.Font(family="Microsoft YaHei", size=10),
            bg=COLORS['secondary'], fg=COLORS['text'], relief=tk.RAISED, bd=2
        ).pack(pady=5)

        # 地图面板
        map_panel = tk.LabelFrame(
            self.widgets['main_frame'], text=" 大地图 ",
            font=tkfont.Font(family="Microsoft YaHei", size=12, weight="bold"),
            fg=COLORS['text'], bg=COLORS['panel'], relief=tk.RAISED, bd=2
        )
        map_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.widgets['map_canvas'] = tk.Canvas(map_panel, width=400, height=300, bg=COLORS['bg'], highlightthickness=0)
        self.widgets['map_canvas'].pack(padx=5, pady=5)

        # 敌人面板
        enemy_panel = tk.LabelFrame(
            self.widgets['main_frame'], text=" 敌人 ",
            font=tkfont.Font(family="Microsoft YaHei", size=12, weight="bold"),
            fg=COLORS['text'], bg=COLORS['panel'], relief=tk.RAISED, bd=2
        )
        enemy_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 0))

        enemy_list_frame = tk.Frame(enemy_panel, bg=COLORS['panel'])
        enemy_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.widgets['enemy_list_label'] = tk.Label(
            enemy_list_frame, text="无敌人",
            font=tkfont.Font(family="Microsoft YaHei", size=11),
            fg=COLORS['text_dim'], bg=COLORS['panel'], wraplength=120
        )
        self.widgets['enemy_list_label'].pack()

    def _create_hand_area(self):
        hand_panel = tk.LabelFrame(
            self.root, text=" 手牌区域 ",
            font=tkfont.Font(family="Microsoft YaHei", size=12, weight="bold"),
            fg=COLORS['text'], bg=COLORS['panel'], relief=tk.RAISED, bd=2
        )
        hand_panel.pack(fill=tk.X, padx=10, pady=5)
        self.widgets['hand_panel'] = hand_panel

        self.widgets['hand_cards_frame'] = tk.Frame(hand_panel, bg=COLORS['panel'])
        self.widgets['hand_cards_frame'].pack(fill=tk.X, padx=10, pady=10)

    def _create_action_buttons(self):
        action_frame = tk.Frame(self.root, bg=COLORS['panel'], relief=tk.RAISED, bd=2)
        action_frame.pack(fill=tk.X, padx=10, pady=5)

        actions = [
            ('调查 (1点)', lambda: [self.game.do_investigate(), self.root.update()]),
            ('攻击 (1点)', lambda: [self.game.do_attack(), self.root.update()]),
            ('移动 (1点)', lambda: [self.game.do_move(), self.root.update()]),
            ('出牌', lambda: [self._show_play_card_dialog(), self.root.update()]),
            ('结束回合', lambda: [self.game.end_investigation_phase(), self.root.update()]),
        ]

        for i, (text, cmd) in enumerate(actions):
            btn = tk.Button(
                action_frame, text=text, command=cmd,
                font=tkfont.Font(family="Microsoft YaHei", size=11),
                bg=COLORS['secondary'], fg=COLORS['text'], relief=tk.RAISED, bd=2,
                width=12, height=2
            )
            btn.pack(side=tk.LEFT, padx=5, pady=5)
            self.widgets[f'btn_{i}'] = btn

    def _create_log_area(self):
        log_panel = tk.LabelFrame(
            self.root, text=" 游戏日志 ",
            font=tkfont.Font(family="Microsoft YaHei", size=12, weight="bold"),
            fg=COLORS['text'], bg=COLORS['panel'], relief=tk.RAISED, bd=2
        )
        log_panel.pack(fill=tk.X, padx=10, pady=5, ipady=3)

        self.widgets['log_text'] = tk.Text(
            log_panel, height=4,
            font=tkfont.Font(family="Microsoft YaHei", size=10),
            bg=COLORS['bg'], fg=COLORS['text'], relief=tk.FLAT
        )
        self.widgets['log_text'].pack(fill=tk.X, padx=5, pady=2)

    def _show_play_card_dialog(self):
        if not self.game.hand:
            return
        if self.game.phase != 1:
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("选择要使用的卡牌")
        dialog.geometry("400x300")
        dialog.configure(bg=COLORS['bg'])
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(
            dialog, text="选择要使用的卡牌:",
            font=tkfont.Font(family="Microsoft YaHei", size=14),
            fg=COLORS['text'], bg=COLORS['bg']
        ).pack(pady=10)

        for i, card in enumerate(self.game.hand):
            type_colors = {'weapon': COLORS['danger'], 'spell': COLORS['mythos'], 'item': COLORS['clue']}
            color = type_colors.get(card.type, COLORS['text'])

            btn_text = f"{card.name} [{card.type}] 消耗:{card.cost}点\n{card.effect}"
            btn = tk.Button(
                dialog, text=btn_text,
                font=tkfont.Font(family="Microsoft YaHei", size=10),
                bg=COLORS['card_bg'], fg=color, relief=tk.RAISED, bd=2,
                width=40, height=2,
                command=lambda idx=i: [self.game.play_card(idx), dialog.destroy()]
            )
            btn.pack(pady=5)

        tk.Button(
            dialog, text="取消",
            command=dialog.destroy,
            font=tkfont.Font(family="Microsoft YaHei", size=11),
            bg=COLORS['secondary'], fg=COLORS['text'], relief=tk.RAISED, bd=2
        ).pack(pady=10)

    # ========== 更新显示 ==========

    def update_display(self):
        g = self.game

        self.widgets['turn_label'].config(text=f"回合: {g.turn}")
        self.widgets['phase_label'].config(text=f"阶段: {g.phase_names[g.phase]}")
        self.widgets['ap_label'].config(text=f"行动点: {g.action_points}/{g.max_action_points}")
        self.widgets['clue_label'].config(text=f"线索: {g.clues}")

        # 调查员属性
        inv = g.investigator
        self.widgets['stats_label'].config(
            text=f"力量: {inv.str}  速度: {inv.spd}\n智慧: {inv.int}  胆识: {inv.wil}"
        )

        # HP条
        self.widgets['hp_text'].config(text=f"{inv.hp}/{inv.max_hp}")
        self._draw_bar(self.widgets['hp_bar'], inv.hp, inv.max_hp, COLORS['danger'])

        # SAN条
        self.widgets['san_text'].config(text=f"{inv.san}/{inv.max_san}")
        self._draw_bar(self.widgets['san_bar'], inv.san, inv.max_san, COLORS['mythos'])

        self.widgets['loc_label'].config(text=f"位置: {inv.location}")

        # 牌组
        self.widgets['deck_label'].config(text=f"牌组: {g.deck.count()}张")
        self.widgets['discard_label'].config(text=f"弃牌堆: {len(g.deck.discard)}张")

        # 敌人
        if g.enemies:
            enemy_text = '\n'.join([f"{e.name} HP:{e.hp} ATK:{e.atk}" for e in g.enemies])
            self.widgets['enemy_list_label'].config(text=enemy_text, fg=COLORS['danger'])
        else:
            self.widgets['enemy_list_label'].config(text="无敌人", fg=COLORS['text_dim'])

        self._draw_scene_cards()
        self._draw_mythos_cards()
        self._draw_hand_cards()
        self._draw_map()
        self._update_buttons()

        # 更新日志
        self._update_log()

    def _draw_bar(self, canvas, current, maximum, color):
        canvas.delete('all')
        bar_width = 95
        bar_height = 12
        fill_width = int(bar_width * current / maximum) if maximum > 0 else 0
        canvas.create_rectangle(0, 0, bar_width, bar_height, fill=COLORS['bg'], outline='')
        canvas.create_rectangle(0, 0, fill_width, bar_height, fill=color, outline='')

    def _draw_scene_cards(self):
        frame = self.widgets['scene_cards_frame']
        for widget in frame.winfo_children():
            widget.destroy()

        for card in self.game.scene_cards:
            card_frame = tk.Frame(frame, bg=COLORS['panel_light'], relief=tk.RAISED, bd=2, width=110)
            card_frame.pack(side=tk.LEFT, padx=4, ipadx=4, ipady=4)
            card_frame.pack_propagate(False)

            if card.completed:
                fg = COLORS['success']
                status = "完成"
            elif card.unlocked:
                fg = COLORS['accent']
                status = "解锁"
            else:
                fg = COLORS['text_dim']
                status = "锁定"

            tk.Label(card_frame, text=card.name, font=tkfont.Font(size=9, weight="bold"),
                     fg=fg, bg=COLORS['panel_light']).pack()
            tk.Label(card_frame, text=f"状态: {status}", font=tkfont.Font(size=8),
                     fg=fg, bg=COLORS['panel_light']).pack()
            tk.Label(card_frame, text=f"线索: {card.clues_current}/{card.clues_needed}",
                     font=tkfont.Font(size=8), fg=COLORS['clue'], bg=COLORS['panel_light']).pack()

    def _draw_mythos_cards(self):
        frame = self.widgets['mythos_cards_frame']
        for widget in frame.winfo_children():
            widget.destroy()

        for card in self.game.mythos_cards:
            card_frame = tk.Frame(frame, bg=COLORS['panel_light'], relief=tk.RAISED, bd=2, width=110)
            card_frame.pack(side=tk.LEFT, padx=4, ipadx=4, ipady=4)
            card_frame.pack_propagate(False)

            tk.Label(card_frame, text=card.name, font=tkfont.Font(size=9, weight="bold"),
                     fg=COLORS['doom'], bg=COLORS['panel_light']).pack()

            doom_str = '◆' * card.doom + '◇' * (card.doom_max - card.doom)
            tk.Label(card_frame, text=f"密谋: {doom_str}", font=tkfont.Font(size=8),
                     fg=COLORS['doom'], bg=COLORS['panel_light']).pack()
            tk.Label(card_frame, text=f"({card.doom}/{card.doom_max})", font=tkfont.Font(size=8),
                     fg=COLORS['text_dim'], bg=COLORS['panel_light']).pack()

    def _draw_hand_cards(self):
        frame = self.widgets['hand_cards_frame']
        for widget in frame.winfo_children():
            widget.destroy()

        for i, card in enumerate(self.game.hand):
            type_colors = {'weapon': COLORS['danger'], 'spell': COLORS['mythos'], 'item': COLORS['clue']}
            color = type_colors.get(card.type, COLORS['text'])

            card_frame = tk.Frame(frame, bg=COLORS['card_bg'], relief=tk.RAISED, bd=2, width=90)
            card_frame.pack(side=tk.LEFT, padx=4, ipadx=4, ipady=4)
            card_frame.pack_propagate(False)

            tk.Label(card_frame, text=card.name, font=tkfont.Font(size=9, weight="bold"),
                     fg=color, bg=COLORS['card_bg']).pack()
            tk.Label(card_frame, text=f"[{card.type}]", font=tkfont.Font(size=7),
                     fg=COLORS['text_dim'], bg=COLORS['card_bg']).pack()
            tk.Label(card_frame, text=f"消耗: {card.cost}点", font=tkfont.Font(size=8),
                     fg=COLORS['text'], bg=COLORS['card_bg']).pack()

    def _draw_map(self):
        canvas = self.widgets['map_canvas']
        canvas.delete('all')

        inv = self.game.investigator

        # 绘制连接线
        for loc1, loc2 in LOCATION_CONNECTIONS:
            x1, y1 = LOCATION_MAP[loc1]
            x2, y2 = LOCATION_MAP[loc2]
            px1, py1 = 40 + x1 * 65, 40 + y1 * 45
            px2, py2 = 40 + x2 * 65, 40 + y2 * 45
            canvas.create_line(px1, py1, px2, py2, fill=COLORS['text_dim'], dash=(3, 3))

        # 绘制地点
        for loc, (x, y) in LOCATION_MAP.items():
            px, py = 40 + x * 65, 40 + y * 45
            is_player = (loc == inv.location)
            fill = COLORS['accent'] if is_player else COLORS['panel_light']

            canvas.create_oval(px - 18, py - 18, px + 18, py + 18, fill=fill, outline=COLORS['text'])
            canvas.create_text(px, py, text=loc, font=tkfont.Font(size=8), fill=COLORS['bg'] if is_player else COLORS['text'])

            # 敌人在此位置
            for j, enemy in enumerate(self.game.enemies):
                if enemy.location == loc:
                    canvas.create_text(px + 20, py - 10 + j * 12, text=f'👹{enemy.name[:3]}',
                                       font=tkfont.Font(size=7), fill=COLORS['danger'])

        # 玩家位置提示
        px, py = LOCATION_MAP[inv.location]
        canvas.create_text(px, py + 32, text='▲ 玩家', font=tkfont.Font(size=8), fill=COLORS['accent'])

    def _update_buttons(self):
        in_investigation = (self.game.phase == 1)
        has_ap = self.game.action_points >= 1

        self.widgets['btn_0'].config(state=tk.NORMAL if (in_investigation and has_ap) else tk.DISABLED)
        self.widgets['btn_1'].config(state=tk.NORMAL if (in_investigation and has_ap and self.game.enemies) else tk.DISABLED)
        self.widgets['btn_2'].config(state=tk.NORMAL if (in_investigation and has_ap) else tk.DISABLED)
        self.widgets['btn_3'].config(state=tk.NORMAL if (in_investigation and has_ap and self.game.hand) else tk.DISABLED)
        self.widgets['btn_4'].config(state=tk.NORMAL if in_investigation else tk.DISABLED)

    def _update_log(self):
        log_text = self.widgets['log_text']
        log_text.delete('1.0', tk.END)
        for msg in self.game.logs[-20:]:  # 只显示最近20条
            log_text.insert(tk.END, msg + '\n')
        log_text.see(tk.END)
