# models.py - 游戏对象模型

from constants import LOCATIONS

# ========== 调查员 ==========
class Investigator:
    def __init__(self, name="调查员"):
        self.name = name
        self.str = 3
        self.spd = 3
        self.int = 4
        self.wil = 3
        self.hp = 10
        self.max_hp = 10
        self.san = 8
        self.max_san = 8
        self.location = '酒馆'

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def lose_sanity(self, amount):
        self.san = max(0, self.san - amount)

    def restore_sanity(self, amount):
        self.san = min(self.max_san, self.san + amount)

    def is_alive(self):
        return self.hp > 0 and self.san > 0

    def get_dodge_chance(self):
        return self.spd * 0.1


# ========== 敌人 ==========
class Enemy:
    def __init__(self, name, hp, atk, location=None):
        self.name = name
        self.hp = hp
        self.atk = atk
        self.location = location or LOCATIONS[0]

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)
        return self.hp <= 0

    def is_alive(self):
        return self.hp > 0


# ========== 卡牌 ==========
class Card:
    def __init__(self, name, card_type, cost, effect):
        self.name = name
        self.type = card_type  # weapon, spell, item
        self.cost = cost
        self.effect = effect

    @staticmethod
    def from_dict(data):
        return Card(data['name'], data['type'], data['cost'], data['effect'])


# ========== 场景卡 ==========
class SceneCard:
    def __init__(self, name, clues_needed):
        self.name = name
        self.clues_needed = clues_needed
        self.clues_current = 0
        self.unlocked = False
        self.completed = False

    def add_clue(self):
        if self.unlocked and not self.completed:
            self.clues_current += 1
            if self.clues_current >= self.clues_needed:
                self.completed = True
                return True
        return False

    def reset(self):
        self.clues_current = 0
        self.unlocked = False
        self.completed = False


# ========== 密谋卡 ==========
class MythosCard:
    def __init__(self, name, doom_max):
        self.name = name
        self.doom = 0
        self.doom_max = doom_max
        self.effect_triggered = False

    def add_doom(self):
        if not self.effect_triggered:
            self.doom += 1
            if self.doom >= self.doom_max:
                self.effect_triggered = True
                return True
        return False

    def reset(self):
        self.doom = 0
        self.effect_triggered = False


# ========== 牌组 ==========
class Deck:
    def __init__(self, cards_data):
        self.cards = [Card.from_dict(c) for c in cards_data]
        self.discard = []
        self._shuffle()

    def _shuffle(self):
        import random
        random.shuffle(self.cards)

    def draw(self):
        if not self.cards:
            return None
        card = self.cards.pop(0)
        return card

    def discard_card(self, card):
        self.discard.append(card)

    def reshuffle_discard(self):
        self.cards.extend(self.discard)
        self.discard = []
        self._shuffle()

    def count(self):
        return len(self.cards)
