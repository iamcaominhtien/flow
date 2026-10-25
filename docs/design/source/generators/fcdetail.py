# Detailed (illustrated) icons: 64 grid, 2.5 ink outline, base + shade + highlight tones, small accents.
K = '#0F172A'
SH = 'fill="rgba(15,23,42,0.13)"'
def S(extra=''): return f'stroke="{K}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round" {extra}'
D = {}
D['Card'] = f'''
<ellipse cx="32" cy="57" rx="22" ry="3.5" {SH}/>
<g transform="rotate(8 32 32)"><rect x="9" y="10" width="46" height="32" rx="6" fill="#FFE2B0" {S()}/></g>
<g transform="rotate(-8 32 32)">
<rect x="6" y="16" width="52" height="34" rx="6" fill="#DCEEFB" {S()}/>
<path d="M6 40h52v4a6 6 0 0 1-6 6H12a6 6 0 0 1-6-6z" fill="#B8D6F2"/>
<rect x="6" y="24" width="52" height="9" fill="#1D4ED8" stroke="{K}" stroke-width="2.5"/>
<path d="M10 21c12-3 26-3 44 0" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" opacity=".8"/>
<rect x="12" y="37" width="11" height="8" rx="2" fill="#FFE2B0" stroke="{K}" stroke-width="2"/><path d="M12 41h11M17.5 37v8" stroke="{K}" stroke-width="1.4" fill="none"/>
<circle cx="32" cy="41" r="1.7" fill="{K}"/><circle cx="38" cy="41" r="1.7" fill="{K}"/><circle cx="44" cy="41" r="1.7" fill="{K}"/><circle cx="50" cy="41" r="1.7" fill="{K}"/>
<rect x="6" y="16" width="52" height="34" rx="6" fill="none" {S()}/></g>'''
D['Restaurant'] = f'''
<ellipse cx="32" cy="58" rx="26" ry="3.5" {SH}/>
<path d="M10 28h44v28H10z" fill="#FFFFFF" {S()}/><path d="M44 28h10v28H44z" fill="#E2E8F0" {S()}/><path d="M10 28h44v28H10z" fill="none" {S()}/>
<rect x="13" y="35" width="11" height="11" rx="1.5" fill="#DCEEFB" {S('stroke-width="2"')}/><path d="M15 38l5-1" stroke="#fff" stroke-width="2" stroke-linecap="round"/>
<rect x="40" y="35" width="11" height="11" rx="1.5" fill="#DCEEFB" {S('stroke-width="2"')}/>
<path d="M26 56V38a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v18z" fill="#F59E3A" {S()}/><circle cx="35" cy="47" r="1.4" fill="{K}"/>
<path d="M6 10h52l5 15H1z" fill="#D92D20" {S()}/>
<path d="M19 10l-3 15M32 10v15M45 10l3 15M26 10l-1 15M39 10l1 15" stroke="none"/>
<path d="M14 10l-4 15h8l2-15zM30 10l-2 15h8l-2-15zM46 10l2 15h8L52 10z" fill="#FFFFFF" stroke="none"/>
<path d="M1 25a6.3 6.3 0 0 0 12.6 0 6.3 6.3 0 0 0 12.6 0 6.3 6.3 0 0 0 12.6 0 6.3 6.3 0 0 0 12.6 0 6.3 6.3 0 0 0 12.6 0" fill="#FFFFFF" {S()}/>
<path d="M6 10h52l5 15H1z" fill="none" {S()}/>'''
D['Pot'] = f'''
<ellipse cx="32" cy="58" rx="22" ry="3.5" {SH}/>
<path d="M18 17c-4 4 4 6 0 11M30 12c-4 4 4 6 0 11M42 17c-4 4 4 6 0 11" fill="none" stroke="#94A3B8" stroke-width="3" stroke-linecap="round"/>
<circle cx="22" cy="30" r="4" fill="#15803D" stroke="{K}" stroke-width="2"/><circle cx="33" cy="29" r="4.5" fill="#D92D20" stroke="{K}" stroke-width="2"/><circle cx="43" cy="30.5" r="3.6" fill="#FFE2B0" stroke="{K}" stroke-width="2"/>
<path d="M4 38h6M54 38h6" {S('stroke-width="4"')}/>
<path d="M9 35h46v7a17 17 0 0 1-17 17H26A17 17 0 0 1 9 42z" fill="#F59E3A" {S()}/>
<path d="M42 35h13v7a17 17 0 0 1-9 15l-4 2z" fill="#E07B12"/>
<path d="M9 35h46v7a17 17 0 0 1-17 17H26A17 17 0 0 1 9 42z" fill="none" {S()}/>
<path d="M15 41c0 5 3 9 7 11" fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round" opacity=".7"/>
<rect x="7" y="31" width="50" height="8" rx="4" fill="#FFE2B0" {S()}/>'''
D['Courier'] = f'''
<ellipse cx="32" cy="58" rx="28" ry="3" {SH}/>
<path d="M2 28h8M0 34h10M3 40h7" stroke="#94A3B8" stroke-width="2.5" stroke-linecap="round"/>
<rect x="12" y="14" width="24" height="22" rx="3.5" fill="#F59E3A" {S()}/>
<path d="M12 22h24" {S('stroke-width="2"')}/><path d="M26 14h10v8H26z" fill="#E07B12" stroke="none"/><rect x="12" y="14" width="24" height="22" rx="3.5" fill="none" {S()}/>
<circle cx="24" cy="29" r="3.4" fill="#FFFFFF" stroke="{K}" stroke-width="2"/>
<path d="M18 46h22c5 0 8-3 8-7v-4h-9l-3 7H18z" fill="#7DD3CB" {S()}/>
<path d="M48 49L43 20M38 20h10" fill="none" {S('stroke-width="3"')}/>
<circle cx="15" cy="49" r="8" fill="#334155" {S()}/><circle cx="15" cy="49" r="3.4" fill="#E2E8F0" stroke="{K}" stroke-width="2"/>
<circle cx="49" cy="49" r="8" fill="#334155" {S()}/><circle cx="49" cy="49" r="3.4" fill="#E2E8F0" stroke="{K}" stroke-width="2"/>
<path d="M14 39h8" stroke="{K}" stroke-width="2" fill="none"/>'''
D['Cart'] = f'''
<ellipse cx="34" cy="59" rx="22" ry="3" {SH}/>
<path d="M2 8h9l8 34h30l8-26H15" fill="none" {S('stroke-width="3"')}/>
<path d="M15 16h42l-8 26H21z" fill="#FFF1DD" {S()}/><path d="M50 16h7l-8 26h-7z" fill="#FFE2B0"/><path d="M15 16h42l-8 26H21z" fill="none" {S()}/>
<rect x="23" y="22" width="11" height="13" rx="2" fill="#DCEEFB" {S('stroke-width="2"')}/><path d="M26 25h5" stroke="#fff" stroke-width="2" stroke-linecap="round"/>
<circle cx="43" cy="31" r="6.5" fill="#15803D" stroke="{K}" stroke-width="2.2"/><path d="M43 24c0-3 2-4 4-4" stroke="{K}" stroke-width="2" fill="none" stroke-linecap="round"/><path d="M40 29c1-2 2-2 3-2" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/>
<circle cx="25" cy="52" r="5" fill="#FFFFFF" {S()}/><circle cx="46" cy="52" r="5" fill="#FFFFFF" {S()}/><circle cx="25" cy="52" r="1.6" fill="{K}"/><circle cx="46" cy="52" r="1.6" fill="{K}"/>'''
D['Mobile'] = f'''
<ellipse cx="32" cy="60" rx="14" ry="2.6" {SH}/>
<rect x="17" y="3" width="30" height="55" rx="8" fill="#DCEEFB" {S()}/><path d="M38 3h1a8 8 0 0 1 8 8v39a8 8 0 0 1-8 8h-1z" fill="#B8D6F2" opacity=".7"/><rect x="17" y="3" width="30" height="55" rx="8" fill="none" {S()}/>
<rect x="21.5" y="10" width="21" height="38" rx="2.5" fill="#FFFFFF" {S('stroke-width="2"')}/>
<rect x="24" y="13" width="16" height="6" rx="1.5" fill="#1D4ED8"/><rect x="24" y="22" width="16" height="9" rx="2" fill="#FFF1DD"/><circle cx="29" cy="26.5" r="2.4" fill="#F59E3A"/><rect x="33" y="24" width="5" height="1.8" fill="#94A3B8"/><rect x="33" y="27.5" width="4" height="1.8" fill="#CBD5E1"/>
<rect x="24" y="33" width="16" height="9" rx="2" fill="#DCF5E1"/><circle cx="29" cy="37.5" r="2.4" fill="#15803D"/><rect x="33" y="35" width="5" height="1.8" fill="#94A3B8"/><rect x="33" y="38.5" width="4" height="1.8" fill="#CBD5E1"/>
<path d="M24 45h16" stroke="#E2E8F0" stroke-width="2.5" stroke-linecap="round"/>
<path d="M23 12l8-2-6 36-2 0z" fill="#fff" opacity=".35"/>
<circle cx="32" cy="53" r="2.2" fill="#fff" stroke="{K}" stroke-width="2"/>'''
D['Bell'] = f'''
<ellipse cx="30" cy="59" rx="15" ry="2.6" {SH}/>
<path d="M30 6c-11 0-16 8-16 18v12l-6 8h44l-6-8V24c0-10-5-18-16-18z" fill="#F59E3A" {S()}/>
<path d="M36 7c8 3 10 10 10 17v12l6 8H38l-2-1z" fill="#E07B12" opacity=".8"/>
<path d="M30 6c-11 0-16 8-16 18v12l-6 8h44l-6-8V24c0-10-5-18-16-18z" fill="none" {S()}/>
<path d="M19 22c1-6 5-10 10-11" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".75"/>
<circle cx="30" cy="5" r="3.5" fill="#FFE2B0" stroke="{K}" stroke-width="2"/>
<path d="M22 48a8 8 0 0 0 16 0z" fill="#FFE2B0" {S()}/>
<circle cx="48" cy="14" r="8.5" fill="#D92D20" stroke="{K}" stroke-width="2.5"/><text x="48" y="18" text-anchor="middle" font-family="Inter, sans-serif" font-size="11" font-weight="800" fill="#fff">1</text>'''
D['Region'] = f'''
<ellipse cx="32" cy="58" rx="16" ry="3.6" {SH}/>
<path d="M32 3C20 3 12 12 12 23c0 15 20 34 20 34s20-19 20-34C52 12 44 3 32 3z" fill="#D92D20" {S()}/>
<path d="M32 3c12 0 20 9 20 20 0 15-20 34-20 34z" fill="#B42318" opacity=".55"/>
<path d="M32 3C20 3 12 12 12 23c0 15 20 34 20 34s20-19 20-34C52 12 44 3 32 3z" fill="none" {S()}/>
<circle cx="32" cy="23" r="8.5" fill="#FFFFFF" {S()}/>
<path d="M19 15c2-4 5-6 9-7" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".7"/>'''
D['Package'] = f'''
<ellipse cx="32" cy="59" rx="24" ry="3.2" {SH}/>
<path d="M32 6l25 11-25 11L7 17z" fill="#FFE2B0" {S()}/>
<path d="M7 17l25 11v31L7 48z" fill="#FFC970" {S()}/>
<path d="M57 17L32 28v31l25-11z" fill="#F59E3A" {S()}/>
<path d="M19.5 11.5l25 11v9l-6 2.7V25z" fill="#DCEEFB" {S('stroke-width="2"')}/>
<path d="M44 38l9-4v8l-9 4z" fill="#FFFFFF" {S('stroke-width="2"')}/><path d="M46 40l5-2M46 43l4-2" stroke="{K}" stroke-width="1.6" fill="none" stroke-linecap="round"/>
<path d="M11 21l7 3" stroke="#fff" stroke-width="2.5" stroke-linecap="round" opacity=".8"/>'''
D['Money'] = f'''
<ellipse cx="32" cy="59" rx="24" ry="3.4" {SH}/>
<g transform="rotate(-10 30 18)"><rect x="6" y="6" width="44" height="24" rx="4" fill="#DCF5E1" {S()}/><circle cx="28" cy="18" r="6.5" fill="#FFFFFF" {S('stroke-width="2"')}/><path d="M28 14.5v7M25.5 17c0-2 5-2 5 0s-5 1.5-5 3.5" stroke="#15803D" stroke-width="1.8" fill="none" stroke-linecap="round"/><circle cx="12" cy="12" r="1.8" fill="#15803D"/><circle cx="44" cy="24" r="1.8" fill="#15803D"/></g>
<path d="M14 52v-6c0-3 8-5 18-5s18 2 18 5v6c0 3-8 5-18 5s-18-2-18-5z" fill="#F59E3A" {S()}/><path d="M14 46c0 3 8 5 18 5s18-2 18-5" fill="none" {S('stroke-width="2"')}/>
<path d="M14 42v-6c0-3 8-5 18-5s18 2 18 5v6c0 3-8 5-18 5s-18-2-18-5z" fill="#FFC970" {S()}/><path d="M14 36c0 3 8 5 18 5s18-2 18-5" fill="none" {S('stroke-width="2"')}/>
<path d="M14 32v-6c0-3 8-5 18-5s18 2 18 5v6c0 3-8 5-18 5s-18-2-18-5z" fill="#FFE2B0" {S()}/><ellipse cx="32" cy="26" rx="18" ry="5" fill="#FFF1DD" {S()}/>
<text x="32" y="29.5" text-anchor="middle" font-family="Inter, sans-serif" font-size="9" font-weight="800" fill="#B45309">$</text>'''
D['Success'] = f'''
<ellipse cx="32" cy="60" rx="18" ry="2.8" {SH}/>
<circle cx="32" cy="31" r="26" fill="#15803D" {S()}/>
<path d="M32 5a26 26 0 0 1 0 52 26 26 0 0 0 0-52z" fill="#0F6B30" opacity=".5"/>
<circle cx="32" cy="31" r="26" fill="none" {S()}/>
<path d="M16 22c3-6 8-10 15-11" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".6"/>
<path d="M19 32l9 9 17-19" fill="none" stroke="#fff" stroke-width="6.5" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="57" cy="9" r="2.6" fill="#F59E3A"/><circle cx="7" cy="12" r="2.2" fill="#5B4BD6"/><path d="M56 50l3 3M59 50l-3 3" stroke="#7DD3CB" stroke-width="2.5" stroke-linecap="round"/>'''
D['Refund'] = f'''
<ellipse cx="38" cy="59" rx="20" ry="3" {SH}/>
<circle cx="38" cy="34" r="20" fill="#FFE2B0" {S()}/><path d="M38 14a20 20 0 0 1 0 40 20 20 0 0 0 0-40z" fill="#FFC970" opacity=".7"/><circle cx="38" cy="34" r="20" fill="none" {S()}/>
<circle cx="38" cy="34" r="13" fill="#FFF1DD" {S('stroke-width="2"')}/>
<text x="38" y="39" text-anchor="middle" font-family="Inter, sans-serif" font-size="17" font-weight="800" fill="#B45309">$</text>
<path d="M30 6A26 26 0 0 0 6 32" fill="none" stroke="#1D4ED8" stroke-width="5.5" stroke-linecap="round"/>
<path d="M-1 28h14l-7 12z" fill="#1D4ED8" stroke="{K}" stroke-width="2.2" stroke-linejoin="round"/>
<path d="M22 11c-4 1-7 3-10 6" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" opacity=".6"/>'''

D['Warning'] = f'''
<ellipse cx="32" cy="59" rx="22" ry="3.2" {SH}/>
<path d="M32 5L61 54H3z" fill="#FFE2B0" {S()}/>
<path d="M32 5l29 49H36z" fill="#FFC970" opacity=".8"/>
<path d="M32 5L61 54H3z" fill="none" {S()}/>
<path d="M32 21v18" stroke="{K}" stroke-width="5" stroke-linecap="round"/><circle cx="32" cy="47" r="3" fill="{K}"/>
<path d="M19 38l8-14" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".8"/>'''
D['Error'] = f'''
<ellipse cx="32" cy="60" rx="18" ry="2.8" {SH}/>
<circle cx="32" cy="31" r="26" fill="#D92D20" {S()}/>
<path d="M32 5a26 26 0 0 1 0 52 26 26 0 0 0 0-52z" fill="#B42318" opacity=".5"/>
<circle cx="32" cy="31" r="26" fill="none" {S()}/>
<path d="M16 22c3-6 8-10 15-11" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".6"/>
<path d="M21 20l22 22M43 20L21 42" stroke="#fff" stroke-width="6.5" stroke-linecap="round"/>'''
D['Approved doc'] = f'''
<ellipse cx="30" cy="60" rx="18" ry="2.8" {SH}/>
<path d="M12 4h28l12 12v40H12z" fill="#FFFFFF" {S()}/>
<path d="M40 4v12h12z" fill="#DCEEFB" {S()}/>
<path d="M44 16v40H34l-2-2z" fill="#E2E8F0" opacity=".7"/><path d="M12 4h28l12 12v40H12z" fill="none" {S()}/>
<path d="M19 24h18M19 31h24M19 38h14" stroke="#94A3B8" stroke-width="3" stroke-linecap="round"/>
<circle cx="44" cy="46" r="12" fill="#15803D" {S()}/><path d="M44 34a12 12 0 0 1 0 24z" fill="#0F6B30" opacity=".5"/><circle cx="44" cy="46" r="12" fill="none" {S()}/>
<path d="M38 46l4 4 7-8" fill="none" stroke="#fff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>'''
def detail(name, size, x=0, y=0, absolute=True):
    pos = f'position:absolute;left:{x}px;top:{y}px;' if absolute else ''
    return f'<svg width="{size}" height="{size}" viewBox="0 0 64 64" style="{pos}overflow:visible" aria-hidden="true">{D[name]}</svg>'
