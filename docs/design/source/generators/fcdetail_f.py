import math
from fcdetail import D, S, SH, K
from fcdetail_d import gear, pie, poly
def cube(cx, cy, s, top, left, right):
    h = s * 0.5
    return (f'<path d="M{cx} {cy-s}l{s} {h}v{s}l-{s} {h}-{s}-{h}v-{s}z" fill="{left}" {S("stroke-width=\"2.2\"")}/>'
            f'<path d="M{cx} {cy-s}l{s} {h}-{s} {h}-{s}-{h}z" fill="{top}" {S("stroke-width=\"2.2\"")}/>'
            f'<path d="M{cx+s} {cy-s+h}v{s}l-{s} {h}v-{s}z" fill="{right}" {S("stroke-width=\"2.2\"")}/>')
D['Calendar'] = f'''
<ellipse cx="32" cy="61" rx="24" ry="2.6" {SH}/>
<rect x="4" y="9" width="56" height="48" rx="8" fill="#FFFFFF" {S()}/><path d="M44 9h8a8 8 0 0 1 8 8v32a8 8 0 0 1-8 8H42z" fill="#E2E8F0" opacity=".6"/>
<path d="M4 17a8 8 0 0 1 8-8h40a8 8 0 0 1 8 8v10H4z" fill="#D92D20" {S()}/>
<rect x="4" y="9" width="56" height="48" rx="8" fill="none" {S()}/>
<path d="M18 3v12M46 3v12" stroke="{K}" stroke-width="5" stroke-linecap="round"/><path d="M18 3v12M46 3v12" stroke="#CBD5E1" stroke-width="2" stroke-linecap="round"/>
<g fill="#94A3B8"><circle cx="15" cy="36" r="2.200"/><circle cx="26" cy="36" r="2.200"/><circle cx="37" cy="36" r="2.200"/><circle cx="49" cy="36" r="2.200"/><circle cx="15" cy="47" r="2.200"/><circle cx="26" cy="47" r="2.200"/><circle cx="49" cy="47" r="2.200"/></g>
<circle cx="37" cy="47" r="6" fill="#1D4ED8" stroke="{K}" stroke-width="2"/><path d="M34 47l2.500 2.500 4.500-5" fill="none" stroke="#fff" stroke-width="2.200" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M10 16h18" stroke="#fff" stroke-width="2.500" stroke-linecap="round" opacity=".7"/>'''
D['Bar chart'] = f'''
<ellipse cx="32" cy="61" rx="26" ry="2.6" {SH}/>
<rect x="3" y="4" width="58" height="53" rx="8" fill="#FFFFFF" {S()}/><path d="M44 4h9a8 8 0 0 1 8 8v37a8 8 0 0 1-8 8H44z" fill="#E2E8F0" opacity=".6"/><rect x="3" y="4" width="58" height="53" rx="8" fill="none" {S()}/>
<path d="M10 49h44" stroke="{K}" stroke-width="2.500" stroke-linecap="round"/>
<rect x="12" y="32" width="9" height="17" rx="2" fill="#1D4ED8" {S('stroke-width="2.200"')}/><rect x="25" y="22" width="9" height="27" rx="2" fill="#15803D" {S('stroke-width="2.200"')}/><rect x="38" y="28" width="9" height="21" rx="2" fill="#F59E3A" {S('stroke-width="2.200"')}/>
<path d="M13 22l12-9 11 5 15-10" fill="none" stroke="#D92D20" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><path d="M45 8h7v7" fill="none" stroke="#D92D20" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M13 35h3M26 25h3M39 31h3" stroke="#fff" stroke-width="2" stroke-linecap="round" opacity=".7"/>'''
D['Pie chart'] = f'''
<ellipse cx="32" cy="61" rx="24" ry="2.6" {SH}/>
<path d="{pie(28, 35, 25, 0, 150)}" fill="#1D4ED8" {S()}/>
<path d="{pie(28, 35, 25, 150, 270)}" fill="#15803D" {S()}/>
<g transform="translate(6 -6)"><path d="{pie(28, 35, 25, 270, 360)}" fill="#F59E3A" {S()}/></g>
<path d="M28 35 28 13" stroke="none"/>
<path d="M14 24c3-5 8-8 14-9" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".7"/>
<path d="M16 49c5 6 14 7 21 4" fill="none" stroke="#fff" stroke-width="2.500" stroke-linecap="round" opacity=".45"/>'''
D['Kubernetes'] = f'''
<ellipse cx="32" cy="61" rx="22" ry="2.6" {SH}/>
<path d="{poly(32, 31, 29, 7)}" fill="#1D4ED8" {S()}/>
<path d="M32 2C46 4 58 22 55 40 45 56 22 57 12 45z" fill="#173FB0" opacity=".45"/>
<path d="{poly(32, 31, 29, 7)}" fill="none" {S()}/>
<circle cx="32" cy="31" r="12" fill="none" stroke="#fff" stroke-width="3.500"/><circle cx="32" cy="31" r="4" fill="#fff"/>
<g stroke="#fff" stroke-width="3.500" stroke-linecap="round"><path d="M32 19V10M41 24l8-5M42 34l9 3M36 43l3 9M28 43l-3 9M22 34l-9 3M23 24l-8-5"/></g>
<path d="M14 18c3-5 8-9 14-10" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" opacity=".5"/>'''
D['Batch / scheduler'] = f'''
<ellipse cx="30" cy="61" rx="26" ry="2.6" {SH}/>
<rect x="14" y="3" width="40" height="14" rx="4" fill="#DCF5E1" {S('stroke-width="2.200"')}/><rect x="9" y="12" width="40" height="14" rx="4" fill="#FFF1DD" {S('stroke-width="2.200"')}/><rect x="4" y="21" width="40" height="14" rx="4" fill="#DCEEFB" {S()}/>
<path d="M10 28h18" stroke="{K}" stroke-width="2.500" stroke-linecap="round"/><circle cx="37" cy="28" r="3" fill="#1D4ED8"/>
<circle cx="42" cy="43" r="19" fill="#FFFFFF" {S()}/><path d="M42 24a19 19 0 0 1 0 38z" fill="#E2E8F0" opacity=".8"/><circle cx="42" cy="43" r="19" fill="none" {S()}/>
<circle cx="42" cy="43" r="14" fill="#DCEEFB" stroke="{K}" stroke-width="2"/>
<path d="M42 43V32" stroke="{K}" stroke-width="3.500" stroke-linecap="round"/><path d="M42 43l7 5" stroke="#D92D20" stroke-width="3" stroke-linecap="round"/><circle cx="42" cy="43" r="2.500" fill="{K}"/>
<path d="M32 33c2-3 5-5 8-5" fill="none" stroke="#fff" stroke-width="2.500" stroke-linecap="round" opacity=".9"/>'''
D['Block storage'] = f'''
<ellipse cx="32" cy="61" rx="28" ry="2.8" {SH}/>
{cube(17, 40, 13, '#DCEEFB', '#B8D6F2', '#1D4ED8')}
{cube(47, 40, 13, '#DCF5E1', '#B5EBC1', '#15803D')}
{cube(32, 28, 13, '#FFF1DD', '#FFD9A3', '#F59E3A')}
<path d="M23 20l7 4M9 31l6 3M39 31l6 3" stroke="#fff" stroke-width="2.500" stroke-linecap="round" opacity=".85"/>'''
D['File storage'] = f'''
<ellipse cx="32" cy="61" rx="24" ry="2.8" {SH}/>
<rect x="6" y="3" width="52" height="56" rx="7" fill="#FFF1DD" {S()}/><path d="M44 3h7a7 7 0 0 1 7 7v42a7 7 0 0 1-7 7H44z" fill="#FFE2B0" opacity=".85"/><rect x="6" y="3" width="52" height="56" rx="7" fill="none" {S()}/>
<path d="M6 31h52" {S()}/>
<rect x="14" y="10" width="36" height="14" rx="3" fill="#FFFFFF" {S('stroke-width="2"')}/><path d="M18 17h14" stroke="#94A3B8" stroke-width="3" stroke-linecap="round"/><path d="M36 14h10v7H36z" fill="#F59E3A"/>
<rect x="14" y="38" width="36" height="14" rx="3" fill="#FFFFFF" {S('stroke-width="2"')}/><path d="M18 45h14" stroke="#94A3B8" stroke-width="3" stroke-linecap="round"/><path d="M36 42h10v7H36z" fill="#1D4ED8"/>
<rect x="24" y="27" width="16" height="6" rx="3" fill="#CBD5E1" {S('stroke-width="2"')}/><rect x="24" y="56" width="16" height="0" fill="none"/>'''
D['Backup / archive'] = f'''
<ellipse cx="32" cy="61" rx="26" ry="2.8" {SH}/>
<rect x="4" y="8" width="56" height="17" rx="4" fill="#F59E3A" {S()}/><path d="M44 8h12a4 4 0 0 1 4 4v9a4 4 0 0 1-4 4H44z" fill="#E07B12" opacity=".8"/><rect x="4" y="8" width="56" height="17" rx="4" fill="none" {S()}/>
<path d="M8 25h48v28a4 4 0 0 1-4 4H12a4 4 0 0 1-4-4z" fill="#FFE2B0" {S()}/><path d="M44 25h12v28a4 4 0 0 1-4 4h-8z" fill="#F7C77E" opacity=".7"/><path d="M8 25h48v28a4 4 0 0 1-4 4H12a4 4 0 0 1-4-4z" fill="none" {S()}/>
<rect x="22" y="32" width="20" height="7" rx="3.500" fill="{K}"/><path d="M12 14h18" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".7"/>
<circle cx="48" cy="48" r="13" fill="#1D4ED8" {S()}/><path d="M48 35a13 13 0 0 1 0 26z" fill="#173FB0" opacity=".6"/><circle cx="48" cy="48" r="13" fill="none" {S()}/>
<path d="M42 48a6 6 0 1 0 2-4.500" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round"/><path d="M42 40v5h5" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'''
D['NoSQL database'] = f'''
<ellipse cx="32" cy="61" rx="24" ry="3" {SH}/>
<path d="M9 14v36c0 6 10 10 23 10s23-4 23-10V14z" fill="#D3F3EF" {S()}/><path d="M44 14h11v36c0 5-6 8-14 9.500z" fill="#A8E6DE" opacity=".85"/>
<path d="M9 14v36c0 6 10 10 23 10s23-4 23-10V14" fill="none" {S()}/>
<ellipse cx="32" cy="14" rx="23" ry="8.500" fill="#0F766E" {S()}/><ellipse cx="32" cy="12.500" rx="14" ry="3.500" fill="#fff" opacity=".35"/>
<path d="M24 28c-4 0-4 3-4 6s-2 4-4 4c2 0 4 1 4 4s0 6 4 6M40 28c4 0 4 3 4 6s2 4 4 4c-2 0-4 1-4 4s0 6-4 6" fill="none" stroke="#0F766E" stroke-width="3.500" stroke-linecap="round" stroke-linejoin="round" transform="translate(0 -3) scale(1 .9) translate(0 4)"/>
<circle cx="32" cy="36" r="2.500" fill="#F59E3A"/><circle cx="32" cy="44" r="2.500" fill="#D92D20"/>'''
D['Data warehouse'] = f'''
<ellipse cx="32" cy="61" rx="29" ry="2.8" {SH}/>
<path d="M2 24L32 6l30 18v33H2z" fill="#E6E3FB" {S()}/><path d="M32 6l30 18v33H34z" fill="#CFC8F7" opacity=".8"/><path d="M2 24L32 6l30 18v33H2z" fill="none" {S()}/>
<path d="M2 24L32 6l30 18" fill="none" {S('stroke-width="3"')}/>
<rect x="13" y="30" width="38" height="27" rx="2" fill="#0F172A" {S()}/><path d="M13 36h38M13 42h38M13 48h38" stroke="#334155" stroke-width="2"/>
<rect x="17" y="43" width="12" height="14" rx="1.500" fill="#F59E3A" {S('stroke-width="2"')}/><rect x="31" y="49" width="14" height="8" rx="1.500" fill="#DCEEFB" {S('stroke-width="2"')}/><rect x="33" y="40.500" width="10" height="8.500" rx="1.500" fill="#DCF5E1" {S('stroke-width="2"')}/>
<circle cx="32" cy="19" r="3.500" fill="#fff" stroke="{K}" stroke-width="2"/>'''
D['Virtual network'] = f'''
<ellipse cx="32" cy="61" rx="28" ry="2.8" {SH}/>
<rect x="3" y="5" width="58" height="52" rx="12" fill="#F3F1FD" stroke="{K}" stroke-width="2.500" stroke-dasharray="6 5" stroke-linejoin="round"/>
<path d="M32 22v14M32 36L16 46M32 36l16 10" fill="none" {S('stroke-width="2.500"')}/>
<rect x="21" y="9" width="22" height="16" rx="4" fill="#DCEEFB" {S()}/><circle cx="27" cy="17" r="2.500" fill="#15803D"/><path d="M33 17h6" stroke="{K}" stroke-width="2.500" stroke-linecap="round"/>
<rect x="5" y="40" width="22" height="16" rx="4" fill="#DCEEFB" {S()}/><circle cx="11" cy="48" r="2.500" fill="#15803D"/><path d="M17 48h5" stroke="{K}" stroke-width="2.500" stroke-linecap="round"/>
<rect x="37" y="40" width="22" height="16" rx="4" fill="#DCEEFB" {S()}/><circle cx="43" cy="48" r="2.500" fill="#F59E3A"/><path d="M49 48h5" stroke="{K}" stroke-width="2.500" stroke-linecap="round"/>
<circle cx="32" cy="36" r="4" fill="#5B4BD6" {S('stroke-width="2.200"')}/>'''
