import json, os
H = os.path.dirname(os.path.abspath(__file__))
K, W = '#0F172A', '#FFFFFF'
B, B1, G, G1 = '#1D4ED8', '#DCEEFB', '#15803D', '#DCF5E1'
A, A1, AM, V, V1 = '#F59E3A', '#FFF1DD', '#FFE2B0', '#5B4BD6', '#E6E3FB'
T, T1, R, R1, S = '#7DD3CB', '#D3F3EF', '#D92D20', '#FDE4E4', '#94A3B8'
def rect(x, y, w, h, r=0):
    return (f'M{x+r} {y}h{w-2*r}a{r} {r} 0 0 1 {r} {r}v{h-2*r}a{r} {r} 0 0 1 {-r} {r}h{-(w-2*r)}a{r} {r} 0 0 1 {-r} {-r}v{-(h-2*r)}a{r} {r} 0 0 1 {r} {-r}z') if r else f'M{x} {y}h{w}v{h}h{-w}z'
def circ(cx, cy, r): return f'M{cx-r} {cy}a{r} {r} 0 1 0 {2*r} 0a{r} {r} 0 1 0 {-2*r} 0z'
def F(d, fill): return {'d': d, 'fill': fill, 'stroke': K, 'sw': 2}
def L(d, stroke=K, sw=2): return {'d': d, 'fill': 'none', 'stroke': stroke, 'sw': sw}
LIB = {}
for g in json.load(open(os.path.join(H, 'icons.json')))['groups']:
    for i in g['icons']:
        LIB.setdefault(i['name'], i['shapes'])
# extra icons for the delivery demo, same 48 grid and same palette
LIB['Card'] = [F(rect(4, 10, 40, 28, 5), B1), F('M4 17h40v7H4z', B), L('M10 31h12'), F(rect(32, 28, 8, 6, 1), AM)]
LIB['Restaurant'] = [F('M7 20h34v22H7z', W), F(rect(19, 28, 10, 14, 1), A1), F(rect(10, 26, 6, 7, 1), B1), F(rect(32, 26, 6, 7, 1), B1),
                     F('M6 7h36l4 13H2z', R), L('M17 7l-2 13M24 7v13M31 7l2 13', W, 2)]
LIB['Pot'] = [L('M15 14c-3 3 3 5 0 8M24 11c-3 3 3 5 0 8M33 14c-3 3 3 5 0 8', S, 2.5), L('M8 29H3M40 29h5'), F(rect(8, 25, 32, 17, 6), A), F(rect(6, 23, 36, 5, 2), AM)]
LIB['Courier'] = [F(rect(4, 12, 17, 15, 3), A), L('M12 12v15'), F(circ(11, 37, 6), W), F(circ(38, 37, 6), W), F('M11 37h16l4-14H21z', T), L('M31 23l3-9h7', K, 3), F(circ(11, 37, 2), K), F(circ(38, 37, 2), K)]
LIB['Refund'] = [F(circ(28, 22, 15), AM), F(circ(28, 22, 9), A1), L('M5 40h20', B, 3.5), L('M12 33l-7 7 7 7', B, 3.5)]
LIB['Star'] = [F('M24 4l6 13 14 2-10 10 2 14-12-7-12 7 2-14L4 19l14-2z', AM)]
LIB['Receipt'] = [F('M10 4h28v40l-5-4-5 4-4-4-4 4-5-4-5 4z', W), L('M17 15h14M17 22h14M17 29h8')]
def icon(name, size, x, y):
    sh = ''.join(f'<path d="{s["d"]}" fill="{s["fill"]}" stroke="{s["stroke"]}" stroke-width="{s["sw"]}"/>' for s in LIB[name])
    return f'<svg width="{size}" height="{size}" viewBox="0 0 48 48" style="position:absolute;left:{x}px;top:{y}px;overflow:visible" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{sh}</svg>'
if __name__ == '__main__':
    names = ['Card', 'Restaurant', 'Pot', 'Courier', 'Refund', 'Star', 'Receipt', 'Mobile', 'Cart', 'Money', 'Bell', 'Region', 'Approved doc', 'Warning', 'Success', 'Package']
    html = '<body style="background:#fff;margin:0">' + ''.join(f'<div style="position:relative;display:inline-block;width:110px;height:110px">{icon(n, 80, 15, 5)}<div style="position:absolute;top:90px;width:110px;text-align:center;font:11px sans-serif">{n}</div></div>' for n in names)
    open(H + '/../shots/icons_test.html', 'w').write(html)
