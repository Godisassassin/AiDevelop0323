# constants.py - 游戏常量和配置数据

# ========== 颜色配置 ==========
COLORS = {
    'bg': '#1a1a2e',
    'panel': '#16213e',
    'panel_light': '#1f3460',
    'primary': '#e94560',
    'secondary': '#0f3460',
    'text': '#eaeaea',
    'text_dim': '#8a8a9a',
    'accent': '#f9ed69',
    'success': '#4ecca3',
    'danger': '#ff6b6b',
    'mythos': '#9b59b6',
    'scene': '#3498db',
    'clue': '#f39c12',
    'doom': '#e74c3c',
    'card_bg': '#2c3e50',
    'location': '#27ae60',
}

# ========== 地图数据 ==========
LOCATIONS = ['酒馆', '森林', '古堡', '城镇', '沼泽', '祭坛']

LOCATION_MAP = {
    '酒馆': (1, 3),
    '森林': (2, 1),
    '古堡': (3, 2),
    '城镇': (4, 0),
    '沼泽': (2, 4),
    '祭坛': (4, 3),
}

LOCATION_CONNECTIONS = [
    ('酒馆', '森林'), ('酒馆', '古堡'), ('酒馆', '沼泽'),
    ('森林', '古堡'), ('森林', '祭坛'),
    ('古堡', '城镇'), ('古堡', '祭坛'),
    ('城镇', '祭坛'), ('沼泽', '祭坛')
]

# ========== 调查员初始卡牌 ==========
INVESTIGATOR_CARDS = [
    {'name': '手枪', 'type': 'weapon', 'cost': 1, 'effect': '造成2点伤害'},
    {'name': '灵知', 'type': 'spell', 'cost': 2, 'effect': '回复2点理智'},
    {'name': '线索扫描', 'type': 'item', 'cost': 1, 'effect': '获得1个线索'},
    {'name': '治疗药水', 'type': 'item', 'cost': 1, 'effect': '回复3点生命'},
    {'name': '驱魔', 'type': 'spell', 'cost': 2, 'effect': '对敌人造成3点伤害'},
    {'name': '智慧卷轴', 'type': 'spell', 'cost': 1, 'effect': '获得2个线索'},
    {'name': '勇气之剑', 'type': 'weapon', 'cost': 2, 'effect': '造成4点伤害'},
    {'name': '急救包', 'type': 'item', 'cost': 1, 'effect': '回复2点生命'},
    {'name': '神秘符咒', 'type': 'spell', 'cost': 1, 'effect': '获得1个线索'},
    {'name': '银剑', 'type': 'weapon', 'cost': 2, 'effect': '造成3点伤害'},
]

# ========== 敌人类型 ==========
ENEMY_TYPES = [
    {'name': '克苏鲁仆从', 'hp': 3, 'atk': 2},
    {'name': '深潜者', 'hp': 4, 'atk': 2},
    {'name': '古革巨人', 'hp': 6, 'atk': 3},
    {'name': '修格斯', 'hp': 5, 'atk': 4},
    {'name': '星级野狗', 'hp': 2, 'atk': 1},
    {'name': '疯狂信徒', 'hp': 3, 'atk': 3},
]
