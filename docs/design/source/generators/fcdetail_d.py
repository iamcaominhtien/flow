import math
from fcdetail import D, S, SH, K
def gear(cx, cy, ro, ri, n):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        w = math.pi / n * 0.55
        for da, r in ((-w * 1.0, ri), (-w * 0.65, ro), (w * 0.65, ro), (w * 1.0, ri)):
            pts.append((cx + r * math.cos(a + da), cy + r * math.sin(a + da)))
    return 'M' + 'L'.join(f'{x:.1f} {y:.1f}' for x, y in pts) + 'z'
def pie(cx, cy, r, a0, a1):
    x0, y0 = cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0))
    x1, y1 = cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1))
    large = 1 if (a1 - a0) % 360 > 180 else 0
    return f'M{cx} {cy}L{x0:.1f} {y0:.1f}A{r} {r} 0 {large} 1 {x1:.1f} {y1:.1f}z'
def poly(cx, cy, r, n, rot=-90):
    return 'M' + 'L'.join(f'{cx + r * math.cos(math.radians(rot + 360 * i / n)):.1f} {cy + r * math.sin(math.radians(rot + 360 * i / n)):.1f}' for i in range(n)) + 'z'
def disc(fill, shade, glyph):  # round status badge, like Success
    return f'''<ellipse cx="32" cy="60" rx="18" ry="2.8" {SH}/><circle cx="32" cy="31" r="26" fill="{fill}" {S()}/><path d="M32 5a26 26 0 0 1 0 52 26 26 0 0 0 0-52z" fill="{shade}" opacity=".5"/><circle cx="32" cy="31" r="26" fill="none" {S()}/><path d="M16 22c3-6 8-10 15-11" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".6"/>{glyph}'''
D['Admin'] = D['User'].replace('<ellipse cx="32" cy="60"', '<ellipse cx="32" cy="60"') + f'''
<path d="M20 15l-2-12 9 6 5-8 5 8 9-6-2 12z" fill="#FFC970" stroke="{K}" stroke-width="2.2" stroke-linejoin="round"/><circle cx="32" cy="9" r="2" fill="#D92D20"/>'''
D['ID card'] = f'''
<ellipse cx="32" cy="61" rx="26" ry="2.6" {SH}/>
<path d="M32 0v10" {S('stroke-width="3"')}/><rect x="25" y="7" width="14" height="9" rx="3" fill="#CBD5E1" {S('stroke-width="2.2"')}/>
<rect x="4" y="13" width="56" height="44" rx="8" fill="#FFFFFF" {S()}/><path d="M42 13h10a8 8 0 0 1 8 8v28a8 8 0 0 1-8 8H38z" fill="#E2E8F0" opacity=".7"/>
<path d="M4 21a8 8 0 0 1 8-8h40a8 8 0 0 1 8 8v4H4z" fill="#1D4ED8" {S()}/>
<circle cx="19" cy="36" r="6" fill="#FFE2B0" {S('stroke-width="2.2"')}/><path d="M9 52c0-7 4-10 10-10s10 3 10 10z" fill="#F59E3A" {S('stroke-width="2.2"')}/>
<path d="M36 33h17M36 40h13M36 47h17" stroke="#94A3B8" stroke-width="3.2" stroke-linecap="round"/>'''
D['Info'] = disc('#1D4ED8', '#173FB0', f'<circle cx="32" cy="19" r="4" fill="#fff"/><path d="M32 28v16" stroke="#fff" stroke-width="7" stroke-linecap="round"/>')
D['Start'] = disc('#15803D', '#0F6B30', '<path d="M25 18l20 13-20 13z" fill="#fff" stroke="#fff" stroke-width="4" stroke-linejoin="round"/>')
D['Stop'] = disc('#D92D20', '#B42318', '<rect x="21" y="20" width="22" height="22" rx="4" fill="#fff"/>')
D['Search'] = f'''
<ellipse cx="30" cy="61" rx="22" ry="2.6" {SH}/>
<path d="M41 42l16 16" stroke="{K}" stroke-width="11" stroke-linecap="round"/><path d="M41 42l16 16" stroke="#F59E3A" stroke-width="6" stroke-linecap="round"/>
<circle cx="26" cy="26" r="21" fill="#DCEEFB" {S()}/><path d="M26 5a21 21 0 0 1 0 42z" fill="#B8D6F2" opacity=".6"/>
<circle cx="26" cy="26" r="21" fill="none" stroke="{K}" stroke-width="5"/><circle cx="26" cy="26" r="21" fill="none" stroke="#CBD5E1" stroke-width="1.5"/>
<path d="M14 20c2-5 6-8 11-9" fill="none" stroke="#fff" stroke-width="3.5" stroke-linecap="round" opacity=".9"/>'''
D['Settings'] = f'''
<ellipse cx="32" cy="61" rx="22" ry="2.6" {SH}/>
<clipPath id="gearclip"><path d="{gear(32, 31, 28, 21, 8)}"/></clipPath>
<path d="{gear(32, 31, 28, 21, 8)}" fill="#E2E8F0"/>
<g clip-path="url(#gearclip)"><path d="M34 0H64V62H34z" fill="#CBD5E1" opacity=".7"/></g>
<path d="{gear(32, 31, 28, 21, 8)}" fill="none" {S()}/>
<circle cx="32" cy="31" r="11" fill="#FFFFFF" {S()}/><circle cx="32" cy="31" r="5" fill="#F59E3A" stroke="{K}" stroke-width="2"/>
<path d="M12 22c2-5 5-8 10-10" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round"/>'''
D['Flag'] = f'''
<ellipse cx="22" cy="60" rx="16" ry="2.8" {SH}/>
<path d="M15 58V5" {S('stroke-width="4"')}/><circle cx="15" cy="4.5" r="3.5" fill="#FFC970" stroke="{K}" stroke-width="2.2"/>
<path d="M17 9c9-5 15 5 24 0s14-3 18 0v26c-4-3-9-4-18 0s-15-5-24 0z" fill="#D92D20" {S()}/>
<path d="M41 9c8-3 13-3 18 0v26c-4-3-9-4-18 0z" fill="#B42318" opacity=".55"/>
<path d="M20 15c4-2 8-2 12 0" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".7"/>'''
D['Target'] = f'''
<ellipse cx="30" cy="61" rx="22" ry="2.6" {SH}/>
<circle cx="30" cy="33" r="26" fill="#FFFFFF" {S()}/><circle cx="30" cy="33" r="19" fill="#D92D20" {S('stroke-width="2.2"')}/><circle cx="30" cy="33" r="12" fill="#FFFFFF" {S('stroke-width="2.2"')}/><circle cx="30" cy="33" r="5.5" fill="#D92D20" {S('stroke-width="2.2"')}/>
<path d="M56 6L33 30" stroke="{K}" stroke-width="3.5" stroke-linecap="round"/>
<path d="M49 5l2 6 6 2 3-9zM56 6l5 1-1 7z" fill="#7DD3CB" stroke="{K}" stroke-width="2" stroke-linejoin="round"/>
<path d="M13 22c3-5 7-8 12-9" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".8"/>'''
D['Idea'] = f'''
<ellipse cx="32" cy="61" rx="14" ry="2.6" {SH}/>
<path d="M32 3a20 20 0 0 0-10 37v5h20v-5A20 20 0 0 0 32 3z" fill="#FFE9A8" {S()}/>
<path d="M32 3a20 20 0 0 1 10 37v5h-10z" fill="#FFC970" opacity=".7"/>
<path d="M32 3a20 20 0 0 0-10 37v5h20v-5A20 20 0 0 0 32 3z" fill="none" {S()}/>
<path d="M25 24l7 8 7-8M32 32v12" fill="none" stroke="{K}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" opacity=".7"/>
<rect x="22" y="45" width="20" height="14" rx="4" fill="#94A3B8" {S()}/><path d="M23 50h18M23 55h18" stroke="{K}" stroke-width="2"/>
<path d="M17 14c3-5 7-8 12-9" fill="none" stroke="#fff" stroke-width="3.5" stroke-linecap="round" opacity=".9"/>
<path d="M4 18l6 3M2 30h7M60 18l-6 3M62 30h-7M12 4l4 5M52 4l-4 5" stroke="#F59E3A" stroke-width="2.8" stroke-linecap="round"/>'''
D['Launch'] = f'''
<ellipse cx="32" cy="61" rx="14" ry="2.4" {SH}/>
<path d="M32 62c-4-6-6-9-6-12h12c0 3-2 6-6 12z" fill="#F59E3A" stroke="{K}" stroke-width="2.2" stroke-linejoin="round"/><path d="M32 58c-2-3-3-5-3-7h6c0 2-1 4-3 7z" fill="#FFE2B0"/>
<path d="M24 34L12 46v8l12-6zM40 34l12 12v8l-12-6z" fill="#D92D20" {S()}/>
<path d="M32 2c10 9 12 22 8 44H24C20 24 22 11 32 2z" fill="#FFFFFF" {S()}/>
<path d="M32 2c10 9 12 22 8 44h-8z" fill="#E2E8F0" opacity=".8"/><path d="M32 2c10 9 12 22 8 44H24C20 24 22 11 32 2z" fill="none" {S()}/>
<path d="M32 2c5 4 8 9 9 15H23c1-6 4-11 9-15z" fill="#D92D20" {S('stroke-width="2.2"')}/>
<circle cx="32" cy="27" r="6.5" fill="#DCEEFB" {S()}/><path d="M29 24c1-1.500 3-2 4-1.500" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"/>
<path d="M6 12l1.500 4 4 1.500-4 1.500L6 23l-1.500-4-4-1.500 4-1.500zM56 28l1 3 3 1-3 1-1 3-1-3-3-1 3-1z" fill="#F59E3A" stroke="{K}" stroke-width="1.400" stroke-linejoin="round"/>'''
