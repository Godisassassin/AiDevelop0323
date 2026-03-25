# game_logic.py - 游戏逻辑

import random
from constants import LOCATIONS, LOCATION_CONNECTIONS, INVESTIGATOR_CARDS, ENEMY_TYPES
from models import Investigator, Enemy, SceneCard, MythosCard, Deck


# ========== 游戏状态 ==========
class GameState:
    def __init__(self):
        # 回合信息
        self.turn = 1
        self.phase = 0  # 0:神话, 1:调查, 2:敌军, 3:整备
        self.phase_names = ['神话阶段', '调查阶段', '敌军阶段', '整备阶段']

        # 调查员
        self.investigator = Investigator()

        # 行动点
        self.action_points = 3
        self.max_action_points = 3

        # 线索
        self.clues = 0

        # 牌组
        self.deck = Deck(INVESTIGATOR_CARDS)
        self.hand = []
        self.max_hand = 7

        # 敌人列表
        self.enemies = []

        # 场景卡
        self.scene_cards = [
            SceneCard('古籍研究室', 2),
            SceneCard('古老遗迹', 3),
            SceneCard('疯狂山脉', 4),
            SceneCard('最终对决', 5),
        ]

        # 密谋卡
        self.mythos_cards = [
            MythosCard('古老者的封印', 3),
            MythosCard('克苏鲁的呼唤', 4),
            MythosCard('毁灭降临', 5),
        ]

        # 游戏结束标记
        self.game_over = False
        self.victory = False

        # 日志
        self.logs = []

        # 回调函数（由UI层设置）
        self.on_state_change = None

    # ========== 日志 ==========
    def log(self, msg):
        self.logs.append(msg)
        if self.on_state_change:
            self.on_state_change('log', msg)

    # ========== 抽牌 ==========
    def draw_card(self):
        if len(self.hand) >= self.max_hand:
            self.log("手牌已满！")
            return False
        card = self.deck.draw()
        if card:
            self.hand.append(card)
            self.log(f"抽牌: {card.name}")
            return True
        else:
            self.log("牌组为空！")
            return False

    def play_card(self, card_index):
        if card_index >= len(self.hand):
            return False

        card = self.hand[card_index]
        if self.action_points < card.cost:
            self.log(f"行动点不足！需要{card.cost}点")
            return False

        self.action_points -= card.cost
        self.hand.pop(card_index)
        self.deck.discard_card(card)
        self.log(f"使用卡牌: {card.name} - {card.effect}")

        # 执行卡牌效果
        self._execute_card_effect(card)

        if self.on_state_change:
            self.on_state_change('update', None)

        return True

    def _execute_card_effect(self, card):
        if card.type == 'weapon':
            if self.enemies:
                dmg = 2 if card.cost == 1 else 4
                if self.enemies[0].take_damage(dmg):
                    self.log(f"💀 {self.enemies[0].name} 被消灭！")
                    self.enemies.pop(0)

        elif card.type == 'spell':
            if '伤害' in card.effect and self.enemies:
                if self.enemies[0].take_damage(3):
                    self.log(f"💀 {self.enemies[0].name} 被消灭！")
                    self.enemies.pop(0)
            elif '理智' in card.effect:
                self.investigator.restore_sanity(2)
                self.log("回复 2 点理智")

        elif card.type == 'item':
            if '生命' in card.effect or 'HP' in card.effect:
                heal = 3 if '3' in card.effect else 2
                self.investigator.heal(heal)
                self.log(f"回复 {heal} 点生命")
            elif '线索' in card.effect:
                clue_count = 2 if '2' in card.effect else 1
                self.clues += clue_count
                self.log(f"获得 {clue_count} 个线索")

    # ========== 场景卡解锁 ==========
    def _advance_scene_cards(self):
        for i, card in enumerate(self.scene_cards):
            if not card.unlocked and not card.completed:
                if i == 0 or self.scene_cards[i - 1].completed:
                    card.unlocked = True
                    self.log(f"🔓 场景卡解锁: {card.name}")

    # ========== 阶段逻辑 ==========

    def start_mythos_phase(self):
        self.phase = 0
        self.log("=== 神话阶段 ===")
        self.log("恐怖的力量在蠢蠢欲动...")

        # 密谋卡+1
        for card in self.mythos_cards:
            if not card.effect_triggered:
                triggered = card.add_doom()
                self.log(f"◆ {card.name} 密谋标记+1 ({card.doom}/{card.doom_max})")
                if triggered:
                    self._trigger_mythos_effect(card)

        # 50%概率生成敌人
        if random.random() < 0.5:
            self._spawn_enemy()

        if self.on_state_change:
            self.on_state_change('phase', self.phase)

        # 神话阶段结束后进入调查阶段
        if not self.game_over:
            self.start_investigation_phase()

    def _trigger_mythos_effect(self, card):
        self.log(f"💀 密谋触发: {card.name}")
        if '封印' in card.name:
            dmg = 2
            self.investigator.take_damage(dmg)
            self.log(f"   受到 {dmg} 点伤害！")
        elif '呼唤' in card.name:
            san_dmg = 2
            self.investigator.lose_sanity(san_dmg)
            self.log(f"   失去 {san_dmg} 点理智！")
        else:
            self.investigator.take_damage(3)
            self.investigator.lose_sanity(2)
            self.log(f"   受到严重伤害和理智损失！")

        self._check_game_over()

    def start_investigation_phase(self):
        self.phase = 1
        self.log("=== 调查阶段 ===")
        self.action_points = self.max_action_points
        self.log(f"获得 {self.action_points} 个行动点")
        self._advance_scene_cards()

        if self.on_state_change:
            self.on_state_change('phase', self.phase)

    def start_enemy_phase(self):
        self.phase = 2
        self.log("=== 敌军阶段 ===")

        for enemy in self.enemies[:]:
            if enemy.location == self.investigator.location:
                damage = enemy.atk
                dodge_chance = self.investigator.get_dodge_chance()
                if random.random() < dodge_chance:
                    self.log(f"🏃 你躲开了 {enemy.name} 的攻击！")
                else:
                    self.investigator.take_damage(damage)
                    self.log(f"⚔️ {enemy.name} 攻击了你！造成 {damage} 点伤害")

        if self._check_game_over():
            return

        if self.on_state_change:
            self.on_state_change('phase', self.phase)

    def start_upkeep_phase(self):
        self.phase = 3
        self.log("=== 整备阶段 ===")
        self.investigator.heal(1)
        self.investigator.restore_sanity(1)
        self.log("回复了1点生命和1点理智")

        if self.on_state_change:
            self.on_state_change('phase', self.phase)

    def next_turn(self):
        self.turn += 1
        self.log(f"=== 回合 {self.turn} 开始 ===")
        if self.turn > 1:
            self.start_mythos_phase()
        else:
            self.start_investigation_phase()

    def end_investigation_phase(self):
        """结束调查阶段，自动运转后续阶段"""
        if self.phase != 1:
            return
        self.log("=== 结束调查阶段 ===")
        self.start_enemy_phase()
        if self.game_over:
            return
        self.start_upkeep_phase()
        if self.game_over:
            return
        # 整备阶段结束后，进入下一回合
        self.turn += 1
        self.log(f"=== 回合 {self.turn} 开始 ===")
        if self.turn > 1:
            self.start_mythos_phase()
        else:
            self.start_investigation_phase()
        # 确保UI更新到最终状态
        if self.on_state_change:
            self.on_state_change('update', None)

    def skip_phase(self):
        if self.phase == 1:
            self.end_investigation_phase()

    # ========== 敌人 ==========

    def _spawn_enemy(self):
        enemy_data = random.choice(ENEMY_TYPES)
        location = random.choice(LOCATIONS)
        enemy = Enemy(enemy_data['name'], enemy_data['hp'], enemy_data['atk'], location)
        self.enemies.append(enemy)
        self.log(f"⚔️ {enemy.name} 出现在 {enemy.location}！")

    # ========== 行动 ==========

    def do_investigate(self):
        if self.phase != 1 or self.action_points < 1:
            return False

        self.action_points -= 1
        self.log("🔍 你开始调查...")

        success_chance = 0.4 + (self.investigator.int * 0.1)
        if random.random() < success_chance:
            self.clues += 1
            self.log(f"✅ 调查成功！获得1个线索 (共{self.clues}个)")

            # 检查场景卡完成
            for card in self.scene_cards:
                if card.unlocked and not card.completed:
                    if self.clues >= card.clues_needed:
                        card.add_clue()
                        self.clues -= card.clues_needed
                        self.log(f"🎉 场景卡完成: {card.name}！")
                        self._check_victory()
                        break
        else:
            self.log("❌ 调查没有发现")

        if random.random() < 0.3 and not self.enemies:
            self._spawn_enemy()

        if self.on_state_change:
            self.on_state_change('update', None)

        return True

    def do_attack(self):
        if self.phase != 1 or self.action_points < 1:
            return False

        if not self.enemies:
            self.log("⚠️ 没有敌人")
            return False

        self.action_points -= 1
        damage = self.investigator.str
        enemy = self.enemies[0]
        if enemy.take_damage(damage):
            self.enemies.pop(0)
            self.log(f"💀 {enemy.name} 被消灭！")
        else:
            self.log(f"⚔️ 你攻击了 {enemy.name}！造成 {damage} 点伤害")

        if self.on_state_change:
            self.on_state_change('update', None)

        return True

    def do_move(self):
        if self.phase != 1 or self.action_points < 1:
            return False

        self.action_points -= 1
        current_idx = LOCATIONS.index(self.investigator.location)

        # 获取可移动的位置
        possible = []
        for loc1, loc2 in LOCATION_CONNECTIONS:
            if loc1 == self.investigator.location:
                possible.append(loc2)
            elif loc2 == self.investigator.location:
                possible.append(loc1)

        if possible:
            new_loc = random.choice(possible)
            self.investigator.location = new_loc
            self.log(f"🚶 移动到: {new_loc}")

            # 检查该位置的敌人
            local_enemies = [e for e in self.enemies if e.location == new_loc]
            if not local_enemies:
                # 甩开敌人
                self.enemies = [e for e in self.enemies if e.location != new_loc]

        if self.on_state_change:
            self.on_state_change('update', None)

        return True

    def _check_game_over(self):
        if not self.investigator.is_alive():
            self.game_over = True
            self.log("=" * 40)
            self.log("💀 游戏结束 - 调查员倒下了！")
            self.log("=" * 40)
            if self.on_state_change:
                self.on_state_change('game_over', None)
            return True
        return False

    def _check_victory(self):
        completed = sum(1 for c in self.scene_cards if c.completed)
        if completed >= 3:
            self.victory = True
            self.game_over = True
            self.log("=" * 40)
            self.log("🎉 胜利！你成功阻止了神话的降临！")
            self.log("=" * 40)
            if self.on_state_change:
                self.on_state_change('victory', None)
