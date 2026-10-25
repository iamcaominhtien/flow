from fcdetail import D, S, SH, K
from fcdetail_d import gear
from fcdetail_f import cube
D['Event stream'] = f'''
<ellipse cx="32" cy="61" rx="28" ry="2.6" {SH}/>
<path d="M2 16c8-8 14 8 22 0s14 8 22 0 12 4 16 0" fill="none" stroke="{K}" stroke-width="10" stroke-linecap="round"/><path d="M2 16c8-8 14 8 22 0s14 8 22 0 12 4 16 0" fill="none" stroke="#1D4ED8" stroke-width="5" stroke-linecap="round"/>
<path d="M2 32c8-8 14 8 22 0s14 8 22 0 12 4 16 0" fill="none" stroke="{K}" stroke-width="10" stroke-linecap="round"/><path d="M2 32c8-8 14 8 22 0s14 8 22 0 12 4 16 0" fill="none" stroke="#5B8EF0" stroke-width="5" stroke-linecap="round"/>
<path d="M2 48c8-8 14 8 22 0s14 8 22 0 12 4 16 0" fill="none" stroke="{K}" stroke-width="10" stroke-linecap="round"/><path d="M2 48c8-8 14 8 22 0s14 8 22 0 12 4 16 0" fill="none" stroke="#9BBCF7" stroke-width="5" stroke-linecap="round"/>
<circle cx="16" cy="12" r="5" fill="#F59E3A" {S('stroke-width="2.200"')}/><circle cx="46" cy="28" r="5" fill="#15803D" {S('stroke-width="2.200"')}/><circle cx="26" cy="49" r="5" fill="#D92D20" {S('stroke-width="2.200"')}/><circle cx="54" cy="44" r="4" fill="#F59E3A" {S('stroke-width="2.200"')}/>'''
D['Workflow'] = f'''
<ellipse cx="32" cy="61" rx="28" ry="2.6" {SH}/>
<path d="M32 17v6M32 40v6" fill="none" {S('stroke-width="2.500"')}/><path d="M42 31h6a6 6 0 0 1 6 6v6" fill="none" {S('stroke-width="2.500"')}/><path d="M22 31h-6a6 6 0 0 0-6 6v6" fill="none" {S('stroke-width="2.500"')}/>
<circle cx="32" cy="10" r="8" fill="#DCF5E1" {S()}/><path d="M29 6.500l7 3.500-7 3.500z" fill="#15803D"/>
<path d="M32 23l10 8-10 8-10-8z" fill="#FFF1DD" {S()}/>
<rect x="2" y="43" width="18" height="13" rx="4" fill="#DCEEFB" {S()}/><rect x="44" y="43" width="18" height="13" rx="4" fill="#DCEEFB" {S()}/>
<rect x="22" y="46" width="20" height="10" rx="3" fill="#E6E3FB" {S('stroke-width="2.200"')}/>
<path d="M7 50h8M49 50h8M27 51h10" stroke="{K}" stroke-width="2.200" stroke-linecap="round"/>
<path d="M30 28l2 2 3-4" fill="none" stroke="#B45309" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity="0"/>'''
D['Identity (IAM)'] = f'''
<ellipse cx="32" cy="61" rx="20" ry="2.8" {SH}/>
<path d="M32 2l26 10v18c0 16-11 26-26 31C17 56 6 46 6 30V12z" fill="#DCEEFB" {S()}/><path d="M32 2l26 10v18c0 16-11 26-26 31z" fill="#B8D6F2" opacity=".8"/><path d="M32 2l26 10v18c0 16-11 26-26 31C17 56 6 46 6 30V12z" fill="none" {S()}/>
<circle cx="32" cy="22" r="8" fill="#FFE2B0" {S('stroke-width="2.200"')}/><path d="M17 44c0-8 6-12 15-12s15 4 15 12c-3 3-8 6-15 9-7-3-12-6-15-9z" fill="#1D4ED8" {S('stroke-width="2.200"')}/>
<circle cx="50" cy="48" r="9" fill="#F59E3A" {S('stroke-width="2.200"')}/><circle cx="50" cy="48" r="3" fill="#fff"/><path d="M50 52v7M50 56h4" stroke="{K}" stroke-width="2.500" stroke-linecap="round" opacity="0"/>
<path d="M12 14c3-3 7-5 12-6" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".8"/>'''
D['Secrets'] = f'''
<ellipse cx="32" cy="61" rx="26" ry="2.8" {SH}/>
<rect x="6" y="56" width="10" height="5" rx="2" fill="{K}"/><rect x="48" y="56" width="10" height="5" rx="2" fill="{K}"/>
<rect x="3" y="4" width="58" height="54" rx="9" fill="#94A3B8" {S()}/><path d="M44 4h8a9 9 0 0 1 9 9v36a9 9 0 0 1-9 9H40z" fill="#64748B" opacity=".7"/><rect x="3" y="4" width="58" height="54" rx="9" fill="none" {S()}/>
<rect x="10" y="11" width="44" height="40" rx="6" fill="#E2E8F0" {S('stroke-width="2.200"')}/>
<circle cx="32" cy="31" r="14" fill="#F59E3A" {S()}/><circle cx="32" cy="31" r="9" fill="#FFE2B0" {S('stroke-width="2"')}/>
<path d="M32 17v4M32 41v4M18 31h4M42 31h4M22 21l3 3M42 21l-3 3M22 41l3-3M42 41l-3-3" stroke="{K}" stroke-width="2" stroke-linecap="round"/>
<path d="M32 31l5-5" stroke="{K}" stroke-width="3" stroke-linecap="round"/><circle cx="32" cy="31" r="2.200" fill="{K}"/>
<path d="M13 16c3-3 6-4 10-4" fill="none" stroke="#fff" stroke-width="2.500" stroke-linecap="round" opacity=".8"/>'''
D['Key management'] = f'''
<ellipse cx="32" cy="61" rx="26" ry="2.8" {SH}/>
<clipPath id="kmclip"><path d="{gear(24, 28, 22, 17, 8)}"/></clipPath>
<path d="{gear(24, 28, 22, 17, 8)}" fill="#E2E8F0"/><g clip-path="url(#kmclip)"><path d="M26 0H60V60H26z" fill="#CBD5E1" opacity=".75"/></g>
<path d="{gear(24, 28, 22, 17, 8)}" fill="none" {S()}/>
<circle cx="24" cy="28" r="8" fill="#FFFFFF" {S('stroke-width="2.200"')}/>
<g transform="rotate(35 40 44)"><rect x="34" y="40" width="26" height="9" rx="3.500" fill="#FFC970" {S()}/><path d="M50 49v6h5v-6M57 49v4h4v-4" fill="#FFC970" {S('stroke-width="2.200"')}/>
<circle cx="31" cy="44.500" r="9" fill="#F59E3A" {S()}/><circle cx="31" cy="44.500" r="3.500" fill="#fff" {S('stroke-width="2"')}/></g>'''
D['Monitoring'] = f'''
<ellipse cx="32" cy="61" rx="24" ry="2.6" {SH}/>
<rect x="3" y="4" width="58" height="42" rx="7" fill="#CBD5E1" {S()}/>
<rect x="8" y="9" width="48" height="32" rx="3" fill="#0F172A"/>
<path d="M11 28h9l4-12 7 20 5-14 3 6h9" fill="none" stroke="#7DD3CB" stroke-width="3.500" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M11 14h10M11 18h6" stroke="#475569" stroke-width="2" stroke-linecap="round"/><circle cx="50" cy="14" r="2.500" fill="#15803D"/>
<path d="M30 11l18-2-14 32H18z" fill="#fff" opacity=".1"/>
<path d="M24 46l-3 11h22l-3-11z" fill="#94A3B8" {S('stroke-width="2.200"')}/><rect x="14" y="56" width="36" height="5" rx="2.500" fill="#CBD5E1" {S('stroke-width="2.200"')}/>'''
D['Logging'] = f'''
<ellipse cx="32" cy="61" rx="22" ry="2.6" {SH}/>
<rect x="8" y="5" width="48" height="54" rx="7" fill="#FFFFFF" {S()}/><path d="M42 5h7a7 7 0 0 1 7 7v40a7 7 0 0 1-7 7H40z" fill="#E2E8F0" opacity=".7"/><rect x="8" y="5" width="48" height="54" rx="7" fill="none" {S()}/>
<rect x="22" y="1" width="20" height="9" rx="4" fill="#94A3B8" {S('stroke-width="2.200"')}/>
<circle cx="17" cy="20" r="3" fill="#1D4ED8"/><path d="M24 20h26" stroke="#94A3B8" stroke-width="3.200" stroke-linecap="round"/>
<circle cx="17" cy="30" r="3" fill="#F59E3A"/><path d="M24 30h20" stroke="#F59E3A" stroke-width="3.200" stroke-linecap="round"/>
<circle cx="17" cy="40" r="3" fill="#D92D20"/><path d="M24 40h24" stroke="#D92D20" stroke-width="3.200" stroke-linecap="round"/>
<circle cx="17" cy="50" r="3" fill="#1D4ED8"/><path d="M24 50h14" stroke="#94A3B8" stroke-width="3.200" stroke-linecap="round"/>'''
D['Container registry'] = f'''
<ellipse cx="32" cy="61" rx="28" ry="2.8" {SH}/>
<rect x="3" y="5" width="58" height="54" rx="6" fill="#FFFFFF" {S()}/><path d="M45 5h10a6 6 0 0 1 6 6v42a6 6 0 0 1-6 6H44z" fill="#E2E8F0" opacity=".7"/><rect x="3" y="5" width="58" height="54" rx="6" fill="none" {S()}/>
<path d="M3 32h58" {S('stroke-width="2.200"')}/>
{cube(18, 24, 8, '#DCEEFB', '#B8D6F2', '#1D4ED8')}{cube(34, 24, 8, '#FFF1DD', '#FFD9A3', '#F59E3A')}{cube(50, 24, 8, '#DCF5E1', '#B5EBC1', '#15803D')}
{cube(18, 52, 8, '#E6E3FB', '#CFC8F7', '#5B4BD6')}{cube(34, 52, 8, '#DCEEFB', '#B8D6F2', '#1D4ED8')}
<rect x="43" y="42" width="14" height="10" rx="2" fill="#FFE2B0" {S('stroke-width="2"')}/><path d="M46 47h8" stroke="{K}" stroke-width="2" stroke-linecap="round"/>'''
D['ML model'] = f'''
<ellipse cx="32" cy="61" rx="28" ry="2.6" {SH}/>
<rect x="2" y="4" width="60" height="53" rx="12" fill="#F3F1FD" {S()}/><path d="M44 4h6a12 12 0 0 1 12 12v29a12 12 0 0 1-12 12H38z" fill="#E6E3FB" opacity=".9"/><rect x="2" y="4" width="60" height="53" rx="12" fill="none" {S()}/>
<g stroke="{K}" stroke-width="2" opacity=".8"><path d="M14 20L32 12M14 20L32 30M14 20L32 48M14 40L32 12M14 40L32 30M14 40L32 48M32 12L50 24M32 30L50 24M32 48L50 24M32 12L50 40M32 30L50 40M32 48L50 40"/></g>
<circle cx="14" cy="20" r="6" fill="#1D4ED8" {S('stroke-width="2.200"')}/><circle cx="14" cy="40" r="6" fill="#1D4ED8" {S('stroke-width="2.200"')}/>
<circle cx="32" cy="12" r="6" fill="#F59E3A" {S('stroke-width="2.200"')}/><circle cx="32" cy="30" r="6" fill="#F59E3A" {S('stroke-width="2.200"')}/><circle cx="32" cy="48" r="6" fill="#F59E3A" {S('stroke-width="2.200"')}/>
<circle cx="50" cy="24" r="6" fill="#15803D" {S('stroke-width="2.200"')}/><circle cx="50" cy="40" r="6" fill="#15803D" {S('stroke-width="2.200"')}/>
<path d="M9 14c2-3 4-4 7-4" fill="none" stroke="#fff" stroke-width="2.200" stroke-linecap="round" opacity=".9"/>'''
D['CPU'] = f'''
<ellipse cx="32" cy="61" rx="24" ry="2.6" {SH}/>
<path d="M19 3v9M32 3v9M45 3v9M19 52v9M32 52v9M45 52v9M3 19h9M3 32h9M3 45h9M52 19h9M52 32h9M52 45h9" stroke="{K}" stroke-width="3" stroke-linecap="round"/>
<rect x="9" y="9" width="46" height="46" rx="8" fill="#E2E8F0" {S()}/><path d="M40 9h7a8 8 0 0 1 8 8v30a8 8 0 0 1-8 8H36z" fill="#CBD5E1" opacity=".8"/><rect x="9" y="9" width="46" height="46" rx="8" fill="none" {S()}/>
<rect x="19" y="19" width="26" height="26" rx="4" fill="#1D4ED8" {S()}/><path d="M32 19h9a4 4 0 0 1 4 4v18a4 4 0 0 1-4 4h-9z" fill="#173FB0" opacity=".7"/>
<path d="M25 32h14M32 25v14" stroke="#7DD3CB" stroke-width="3" stroke-linecap="round"/><circle cx="32" cy="32" r="3" fill="#F59E3A"/>
<circle cx="15" cy="15" r="2" fill="{K}"/><path d="M14 24c1-4 4-7 8-8" fill="none" stroke="#fff" stroke-width="2.500" stroke-linecap="round" opacity=".8"/>'''
