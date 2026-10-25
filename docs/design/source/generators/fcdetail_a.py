from fcdetail import D, S, SH, K
# batch 1: people and compute
D['User'] = f'''
<ellipse cx="32" cy="60" rx="20" ry="3" {SH}/>
<path d="M9 59c0-14 10-22 23-22s23 8 23 22z" fill="#1D4ED8" {S()}/>
<path d="M32 37c13 0 23 8 23 22H40c0-9-3-16-8-22z" fill="#173FB0" opacity=".7"/>
<path d="M9 59c0-14 10-22 23-22s23 8 23 22z" fill="none" {S()}/>
<path d="M24 38l8 9 8-9" fill="#FFFFFF" {S('stroke-width="2"')}/>
<circle cx="32" cy="22" r="12.5" fill="#FFE2B0" {S()}/>
<path d="M32 9.5a12.5 12.5 0 0 1 0 25z" fill="#F7C77E" opacity=".6"/>
<path d="M19.6 20c1-9 8-13 14-12 6 1 10 6 9 12-4-2-9-6-12-8-3 4-7 7-11 8z" fill="#334155" {S('stroke-width="2"')}/>
<circle cx="27" cy="24" r="1.7" fill="{K}"/><circle cx="37" cy="24" r="1.7" fill="{K}"/><path d="M28 29c2 2 6 2 8 0" fill="none" stroke="{K}" stroke-width="2" stroke-linecap="round"/>'''
D['Team'] = f'''
<ellipse cx="32" cy="60" rx="28" ry="3" {SH}/>
<path d="M0 56c0-10 6-15 14-15s12 5 12 15z" fill="#15803D" {S()}/><circle cx="14" cy="30" r="7.5" fill="#FFE2B0" {S()}/>
<path d="M38 56c0-10 4-15 12-15s14 5 14 15z" fill="#5B4BD6" {S()}/><circle cx="50" cy="30" r="7.5" fill="#FFE2B0" {S()}/>
<path d="M11 60c0-12 8-19 21-19s21 7 21 19z" fill="#1D4ED8" {S()}/><path d="M32 41c13 0 21 7 21 19H42c0-8-3-14-10-19z" fill="#173FB0" opacity=".7"/>
<circle cx="32" cy="27" r="10.5" fill="#FFE2B0" {S()}/>
<path d="M22 25c1-8 7-11 12-10 5 1 8 5 8 10-4-1-8-4-10-6-2 3-6 5-10 6z" fill="#334155" {S('stroke-width="2"')}/>
<circle cx="28" cy="29" r="1.5" fill="{K}"/><circle cx="36" cy="29" r="1.5" fill="{K}"/><path d="M29 33c2 1.5 4 1.5 6 0" fill="none" stroke="{K}" stroke-width="1.8" stroke-linecap="round"/>'''
D['Bot'] = f'''
<ellipse cx="32" cy="60" rx="20" ry="3" {SH}/>
<path d="M32 15V7" {S('stroke-width="3"')}/><circle cx="32" cy="6" r="3.8" fill="#D92D20" {S()}/>
<rect x="3" y="28" width="7" height="14" rx="3" fill="#F59E3A" {S()}/><rect x="54" y="28" width="7" height="14" rx="3" fill="#F59E3A" {S()}/>
<rect x="9" y="15" width="46" height="40" rx="13" fill="#E6E3FB" {S()}/><path d="M42 15h0a13 13 0 0 1 13 13v14a13 13 0 0 1-13 13h-2z" fill="#CFC8F7" opacity=".8"/><rect x="9" y="15" width="46" height="40" rx="13" fill="none" {S()}/>
<rect x="16" y="24" width="32" height="18" rx="8" fill="#0F172A"/>
<circle cx="25" cy="33" r="4.5" fill="#7DD3CB"/><circle cx="39" cy="33" r="4.5" fill="#7DD3CB"/><circle cx="26.2" cy="31.8" r="1.4" fill="#fff"/><circle cx="40.2" cy="31.8" r="1.4" fill="#fff"/>
<path d="M24 48h16" {S('stroke-width="2"')}/><path d="M28 48v3M32 48v3M36 48v3" stroke="{K}" stroke-width="1.6"/>
<path d="M14 24c2-4 5-6 9-7" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".7"/>'''
def unit(y):
    return f'''<rect x="7" y="{y}" width="50" height="15" rx="4.5" fill="#DCEEFB" {S()}/><path d="M44 {y}h8.5a4.5 4.5 0 0 1 4.5 4.5v6a4.5 4.5 0 0 1-4.5 4.5H44z" fill="#B8D6F2" opacity=".8"/><rect x="7" y="{y}" width="50" height="15" rx="4.5" fill="none" {S()}/><circle cx="15" cy="{y+7.5}" r="2.3" fill="#15803D" stroke="{K}" stroke-width="1.5"/><circle cx="22" cy="{y+7.5}" r="2.3" fill="#F59E3A" stroke="{K}" stroke-width="1.5"/><path d="M31 {y+5}h18M31 {y+10}h12" stroke="{K}" stroke-width="2" stroke-linecap="round"/>'''
D['Server'] = f'<ellipse cx="32" cy="60" rx="26" ry="3" {SH}/>' + unit(5) + unit(23) + unit(41) + '<path d="M11 9c6-1 12-1 20 0" stroke="#fff" stroke-width="2" fill="none" stroke-linecap="round" opacity=".8"/>'
D['Container'] = f'''
<ellipse cx="32" cy="60" rx="28" ry="3" {SH}/>
<path d="M4 18l8-8h48l-8 8z" fill="#F1F5F9" {S()}/>
<path d="M52 18l8-8v34l-8 8z" fill="#B8D6F2" {S()}/>
<rect x="4" y="18" width="48" height="34" fill="#DCEEFB" {S()}/>
<path d="M12 18v34M20 18v34M28 18v34M36 18v34M44 18v34" stroke="#1D4ED8" stroke-width="2.2" opacity=".55"/>
<rect x="4" y="18" width="48" height="6" fill="#1D4ED8" {S()}/>
<rect x="4" y="18" width="48" height="34" fill="none" {S()}/>
<rect x="38" y="36" width="9" height="8" rx="1.5" fill="#FFE2B0" {S('stroke-width="2"')}/><path d="M13 33l4-3" stroke="#fff" stroke-width="2.5" stroke-linecap="round" opacity=".8"/>'''
D['Function'] = f'''
<ellipse cx="32" cy="60" rx="22" ry="3" {SH}/>
<rect x="6" y="5" width="52" height="52" rx="14" fill="#E6E3FB" {S()}/><path d="M44 5h0a14 14 0 0 1 14 14v24a14 14 0 0 1-14 14h-6z" fill="#CFC8F7" opacity=".8"/><rect x="6" y="5" width="52" height="52" rx="14" fill="none" {S()}/>
<path d="M22 18h7c3 0 4 2 5 6l4 20" fill="none" stroke="#5B4BD6" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M30 33l-9 13" fill="none" stroke="#5B4BD6" stroke-width="5" stroke-linecap="round"/>
<path d="M12 14c2-4 5-6 9-7" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".8"/>
<path d="M50 8l2 5 5 2-5 2-2 5-2-5-5-2 5-2z" fill="#F59E3A" stroke="{K}" stroke-width="1.6" stroke-linejoin="round"/>'''
def mini(x, y, w=18, h=14):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3.5" fill="#DCEEFB" {S("stroke-width=\"2.2\"")}/><circle cx="{x+5}" cy="{y+h/2}" r="1.7" fill="#15803D"/><path d="M{x+9} {y+h/2}h{w-13}" stroke="{K}" stroke-width="1.8" stroke-linecap="round"/>'
D['Cluster'] = f'''
<ellipse cx="32" cy="60" rx="28" ry="3" {SH}/>
<path d="M32 22v8M11 40v-6h42v6" fill="none" {S('stroke-width="2.5"')}/><circle cx="32" cy="30" r="2.6" fill="{K}"/>
<rect x="19" y="6" width="26" height="18" rx="5" fill="#E6E3FB" {S()}/><circle cx="26" cy="15" r="2.4" fill="#15803D"/><path d="M32 15h8" stroke="{K}" stroke-width="2.2" stroke-linecap="round"/>
<rect x="1" y="40" width="20" height="16" rx="4.5" fill="#DCEEFB" {S()}/><circle cx="7" cy="48" r="2" fill="#15803D"/><path d="M12 48h5" stroke="{K}" stroke-width="2" stroke-linecap="round"/>
<rect x="43" y="40" width="20" height="16" rx="4.5" fill="#DCEEFB" {S()}/><circle cx="49" cy="48" r="2" fill="#F59E3A"/><path d="M54 48h5" stroke="{K}" stroke-width="2" stroke-linecap="round"/>
<rect x="22" y="40" width="20" height="16" rx="4.5" fill="#DCEEFB" {S()}/><circle cx="28" cy="48" r="2" fill="#15803D"/><path d="M33 48h4" stroke="{K}" stroke-width="2" stroke-linecap="round"/>
<path d="M32 30v10" {S('stroke-width="2.5"')}/>'''
D['Load balancer'] = f'''
<ellipse cx="32" cy="60" rx="28" ry="3" {SH}/>
<rect x="16" y="3" width="32" height="16" rx="5" fill="#F59E3A" {S()}/><path d="M38 3h5a5 5 0 0 1 5 5v6a5 5 0 0 1-5 5h-5z" fill="#E07B12" opacity=".8"/><rect x="16" y="3" width="32" height="16" rx="5" fill="none" {S()}/>
<path d="M22 11h20M26 8l-3 3 3 3M38 8l3 3-3 3" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M32 19v8M9 27h46M9 27v13M32 27v13M55 27v13" fill="none" {S('stroke-width="2.5"')}/>
<path d="M5 38l4 5 4-5zM28 38l4 5 4-5zM51 38l4 5 4-5z" fill="{K}" stroke="{K}" stroke-width="1.5" stroke-linejoin="round"/>
<rect x="0.5" y="44" width="17" height="15" rx="4" fill="#DCEEFB" {S('stroke-width="2.2"')}/><rect x="23.5" y="44" width="17" height="15" rx="4" fill="#DCEEFB" {S('stroke-width="2.2"')}/><rect x="46.5" y="44" width="17" height="15" rx="4" fill="#DCEEFB" {S('stroke-width="2.2"')}/>
<circle cx="9" cy="51.5" r="2" fill="#15803D"/><circle cx="32" cy="51.5" r="2" fill="#15803D"/><circle cx="55" cy="51.5" r="2" fill="#F59E3A"/>'''
D['Gateway'] = f'''
<ellipse cx="32" cy="60" rx="26" ry="3" {SH}/>
<path d="M12 58V28a20 20 0 0 1 40 0v30z" fill="#D3F3EF" {S()}/><path d="M42 12a20 20 0 0 1 10 16v30h-8z" fill="#A8E6DE" opacity=".8"/><path d="M12 58V28a20 20 0 0 1 40 0v30z" fill="none" {S()}/>
<path d="M20 58V30a12 12 0 0 1 24 0v28z" fill="#0F172A" {S()}/>
<path d="M32 18v6M25 23l4 3M39 23l-4 3" stroke="#7DD3CB" stroke-width="2.4" stroke-linecap="round"/>
<path d="M1 44h26" stroke="#1D4ED8" stroke-width="5" stroke-linecap="round"/><path d="M24 36l12 8-12 8z" fill="#1D4ED8" stroke="{K}" stroke-width="2" stroke-linejoin="round"/>
<path d="M17 18c3-5 7-8 12-9" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".7"/>'''
D['Database'] = f'''
<ellipse cx="32" cy="60" rx="24" ry="3" {SH}/>
<path d="M9 14v36c0 6 10 10 23 10s23-4 23-10V14z" fill="#E6E3FB" {S()}/>
<path d="M44 14h11v36c0 5-6 8-14 9.5z" fill="#CFC8F7" opacity=".85"/>
<path d="M9 28c0 5 10 9 23 9s23-4 23-9M9 41c0 5 10 9 23 9s23-4 23-9" fill="none" {S('stroke-width="2.2"')}/>
<path d="M9 14v36c0 6 10 10 23 10s23-4 23-10V14" fill="none" {S()}/>
<ellipse cx="32" cy="14" rx="23" ry="8.5" fill="#5B4BD6" {S()}/><ellipse cx="32" cy="12.5" rx="14" ry="3.5" fill="#fff" opacity=".35"/>
<circle cx="16" cy="33" r="2" fill="#15803D" stroke="{K}" stroke-width="1.3"/><circle cx="16" cy="46" r="2" fill="#F59E3A" stroke="{K}" stroke-width="1.3"/>
<path d="M13 22v18" stroke="#fff" stroke-width="2.5" stroke-linecap="round" opacity=".6" transform="translate(0 -4)"/>'''
