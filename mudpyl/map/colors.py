COLORS = {
    'city': '#669999',
    'field': '#66ff66',
    'hills': '#999966',
    'inside': '#ffcc00',
    'mountain': '#666699',
    'swim water': '#66ccff',
    'forest': '#339933',
    'no swim water': '#0000ff',
    'flying': '#ffccff',
    }

def get_color(name):
    if COLORS.has_key(name):
        return COLORS[name]
    return '#cc3300'
