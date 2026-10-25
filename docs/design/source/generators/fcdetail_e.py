import math
from fcdetail import D, S, SH, K
from fcdetail_d import gear, pie, poly
# batch: data, network, apps, messaging
D['Virtual machine'] = f'''
<ellipse cx="32" cy="61" rx="24" ry="2.8" {SH}/>
<path d="M32 4l25 11v30L32 58 7 45V15z" fill="#E6E3FB" {S()}/>
<path d="M32 4l25 11-25 11L7 15z" fill="#5B4BD6" {S()}/>
<path d="M57 15L32 26v32l25-13z" fill="#CFC8F7" {S()}/>
<path d="M7 15l25 11v32L7 45z" fill="#E6E3FB" {S()}/>
<path d="M32 4l25 11v30L32 58 7 45V15z" fill="none" {S()}/><path d="M7 15l25 11 25-11M32 26v32" fill="none" {S()}/>
<path d="M11 29l17 7.500V46L11 38.500z" fill="#fff" stroke="{K}" stroke-width="2" stroke-linejoin="round"/>
<path d="M14 12l8-3" stroke="#fff" stroke-width="2.5" stroke-linecap="round" opacity=".7"/>
<circle cx="45" cy="38" r="3.4" fill="#15803D" stroke="{K}" stroke-width="1.8"/>'''
D['Table'] = f'''
<ellipse cx="32" cy="61" rx="26" ry="2.6" {SH}/>
<rect x="3" y="6" width="58" height="50" rx="7" fill="#FFFFFF" {S()}/>
<path d="M3 13a7 7 0 0 1 7-7h44a7 7 0 0 1 7 7v10H3z" fill="#15803D" {S()}/>
<path d="M3 34h58M3 45h58M24 23v33M43 23v33" fill="none" stroke="{K}" stroke-width="2"/>
<path d="M44 6h10a7 7 0 0 1 7 7v37a7 7 0 0 1-7 6H44z" fill="#E2E8F0" opacity=".55"/>
<rect x="3" y="6" width="58" height="50" rx="7" fill="none" {S()}/>
<path d="M9 15h10M28 15h10M47 15h9" stroke="#fff" stroke-width="3" stroke-linecap="round"/>
<rect x="26" y="25.500" width="15" height="7" rx="2" fill="#FFE2B0"/><rect x="5" y="36" width="17" height="7" rx="2" fill="#DCEEFB"/>'''
D['JSON'] = f'''
<ellipse cx="32" cy="61" rx="22" ry="2.6" {SH}/>
<rect x="6" y="4" width="52" height="52" rx="10" fill="#FFFFFF" {S()}/><path d="M44 4h4a10 10 0 0 1 10 10v32a10 10 0 0 1-10 10h-10z" fill="#E2E8F0" opacity=".7"/><rect x="6" y="4" width="52" height="52" rx="10" fill="none" {S()}/>
<path d="M26 15c-5 0-5 4-5 8s-2 6-5 6c3 0 5 2 5 6s0 8 5 8" fill="none" stroke="#5B4BD6" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M38 15c5 0 5 4 5 8s2 6 5 6c-3 0-5 2-5 6s0 8-5 8" fill="none" stroke="#5B4BD6" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="32" cy="29" r="2.4" fill="#F59E3A"/><circle cx="32" cy="38" r="2.4" fill="#15803D"/>
<path d="M12 12c3-4 7-6 12-6" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".9"/>'''
D['Data lake'] = f'''
<ellipse cx="32" cy="61" rx="28" ry="2.6" {SH}/>
<rect x="9" y="3" width="13" height="13" rx="2.5" fill="#FFF1DD" {S('stroke-width="2.2"')}/><rect x="26" y="6" width="13" height="13" rx="2.5" fill="#DCF5E1" {S('stroke-width="2.2"')}/><rect x="43" y="2" width="13" height="13" rx="2.5" fill="#E6E3FB" {S('stroke-width="2.2"')}/>
<path d="M15 22v-4M32 25v-4M49 21v-5" stroke="{K}" stroke-width="2.2" stroke-linecap="round"/>
<path d="M3 26c6 5 10-5 17 0s11 5 15 0 12-5 15 0 9 3 11 0v22c0 7-12 11-29 11S3 55 3 48z" fill="#DCEEFB" {S()}/>
<path d="M3 38c6 5 10-5 17 0s11 5 15 0 12-5 15 0 9 3 11 0" fill="none" stroke="#1D4ED8" stroke-width="3" stroke-linecap="round"/>
<path d="M44 26c4-2 8-3 17 0v22c0 4-4 7-10 9z" fill="#B8D6F2" opacity=".7"/>
<path d="M10 30c3 2 6 1 8-1" fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round" opacity=".9"/>'''
D['Wi-Fi'] = f'''
<ellipse cx="32" cy="61" rx="16" ry="2.6" {SH}/>
<path d="M4 25a40 40 0 0 1 56 0" fill="none" stroke="{K}" stroke-width="11" stroke-linecap="round"/><path d="M4 25a40 40 0 0 1 56 0" fill="none" stroke="#1D4ED8" stroke-width="6" stroke-linecap="round"/>
<path d="M13 35a27 27 0 0 1 38 0" fill="none" stroke="{K}" stroke-width="11" stroke-linecap="round"/><path d="M13 35a27 27 0 0 1 38 0" fill="none" stroke="#5B8EF0" stroke-width="6" stroke-linecap="round"/>
<path d="M22 45a14 14 0 0 1 20 0" fill="none" stroke="{K}" stroke-width="11" stroke-linecap="round"/><path d="M22 45a14 14 0 0 1 20 0" fill="none" stroke="#9BBCF7" stroke-width="6" stroke-linecap="round"/>
<circle cx="32" cy="55" r="5.5" fill="#F59E3A" {S()}/>
<path d="M12 19c6-6 14-9 22-8" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" opacity=".7"/>'''
D['DNS'] = f'''
<ellipse cx="32" cy="61" rx="18" ry="2.6" {SH}/>
<rect x="29" y="4" width="6" height="56" rx="2" fill="#94A3B8" {S('stroke-width="2.2"')}/>
<path d="M33 8h22l7 8-7 8H33z" fill="#DCEEFB" {S()}/><path d="M33 8h22l7 8-7 8H33z" fill="none" {S()}/>
<text x="46" y="19.500" text-anchor="middle" font-family="Inter, sans-serif" font-size="9" font-weight="800" fill="#1D4ED8">www</text>
<path d="M31 30H9l-7 8 7 8h22z" fill="#FFF1DD" {S()}/>
<text x="18" y="41.500" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="8.500" font-weight="800" fill="#B45309">1.2.3</text>
<circle cx="32" cy="4" r="3.500" fill="#F59E3A" stroke="{K}" stroke-width="2.2"/>'''
D['Private network'] = f'''
<ellipse cx="32" cy="61" rx="24" ry="2.6" {SH}/>
<path d="M16 46a12 12 0 0 1-2-23.800A16 16 0 0 1 45 24a11 11 0 0 1-2 22z" fill="#DCEEFB" {S()}/><path d="M45 24a11 11 0 0 1-2 22H31c7-3 11-10 9-19 2-4 4-4 5-3z" fill="#B8D6F2" opacity=".85"/><path d="M16 46a12 12 0 0 1-2-23.800A16 16 0 0 1 45 24a11 11 0 0 1-2 22z" fill="none" {S()}/>
<path d="M17 22c3-5 8-8 13-7" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".85"/>
<path d="M32 40v-4a6 6 0 0 1 12 0v4" fill="none" stroke="{K}" stroke-width="6" stroke-linecap="round"/><path d="M32 40v-4a6 6 0 0 1 12 0v4" fill="none" stroke="#CBD5E1" stroke-width="2.600" stroke-linecap="round"/>
<rect x="27" y="38" width="22" height="20" rx="5" fill="#F59E3A" {S()}/><circle cx="38" cy="47" r="3" fill="{K}"/><path d="M38 47v5" stroke="{K}" stroke-width="3" stroke-linecap="round"/>'''
D['Plugin'] = f'''
<ellipse cx="32" cy="61" rx="22" ry="2.6" {SH}/>
<circle cx="27" cy="12" r="8" fill="#E6E3FB" {S()}/><circle cx="55" cy="38" r="8" fill="#E6E3FB" {S()}/>
<rect x="6" y="15" width="44" height="44" rx="8" fill="#E6E3FB" {S()}/><path d="M36 15h6a8 8 0 0 1 8 8v28a8 8 0 0 1-8 8H30z" fill="#CFC8F7" opacity=".8"/><rect x="6" y="15" width="44" height="44" rx="8" fill="none" {S()}/>
<rect x="21" y="13.500" width="12" height="4" fill="#E6E3FB"/><rect x="48.500" y="32" width="4" height="12" fill="#E6E3FB"/>
<circle cx="27" cy="12" r="3" fill="#F59E3A" stroke="{K}" stroke-width="1.8"/>
<path d="M16 28v14M16 35h10" stroke="#5B4BD6" stroke-width="5" stroke-linecap="round"/><circle cx="36" cy="40" r="5" fill="#5B4BD6"/>
<path d="M12 22c2-3 5-4 9-4" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".85"/>'''
D['Dashboard'] = f'''
<ellipse cx="32" cy="61" rx="26" ry="2.6" {SH}/>
<rect x="3" y="5" width="58" height="52" rx="8" fill="#FFFFFF" {S()}/><path d="M44 5h9a8 8 0 0 1 8 8v36a8 8 0 0 1-8 8H44z" fill="#E2E8F0" opacity=".6"/><rect x="3" y="5" width="58" height="52" rx="8" fill="none" {S()}/>
<rect x="9" y="12" width="20" height="14" rx="3" fill="#DCEEFB" {S('stroke-width="2"')}/><path d="M12 22l5-5 4 3 5-6" fill="none" stroke="#1D4ED8" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="45" cy="19" r="8" fill="#FFF1DD" {S('stroke-width="2"')}/><path d="M45 19V11a8 8 0 0 1 8 8z" fill="#F59E3A" stroke="{K}" stroke-width="1.8" stroke-linejoin="round"/>
<rect x="11" y="34" width="8" height="16" rx="1.500" fill="#1D4ED8" {S('stroke-width="2"')}/><rect x="23" y="29" width="8" height="21" rx="1.500" fill="#15803D" {S('stroke-width="2"')}/><rect x="35" y="39" width="8" height="11" rx="1.500" fill="#F59E3A" {S('stroke-width="2"')}/><rect x="47" y="33" width="8" height="17" rx="1.500" fill="#5B4BD6" {S('stroke-width="2"')}/>'''
D['Event'] = f'''
<ellipse cx="32" cy="61" rx="18" ry="2.8" {SH}/>
<circle cx="32" cy="31" r="26" fill="#FFF1DD" {S()}/><path d="M32 5a26 26 0 0 1 0 52 26 26 0 0 0 0-52z" fill="#FFE2B0" opacity=".8"/><circle cx="32" cy="31" r="26" fill="none" {S()}/>
<path d="M36 10L19 34h12l-4 19 19-27H34z" fill="#F59E3A" stroke="{K}" stroke-width="2.600" stroke-linejoin="round"/>
<path d="M16 22c3-6 8-10 15-11" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".8"/>
<path d="M56 6l2 4 4 2-4 2-2 4-2-4-4-2 4-2z" fill="#5B4BD6" stroke="{K}" stroke-width="1.400" stroke-linejoin="round"/>'''
D['Pub / Sub'] = f'''
<ellipse cx="32" cy="61" rx="24" ry="2.6" {SH}/>
<path d="M15 14a24 24 0 0 0 0 34M49 14a24 24 0 0 1 0 34" fill="none" stroke="{K}" stroke-width="9" stroke-linecap="round"/><path d="M15 14a24 24 0 0 0 0 34M49 14a24 24 0 0 1 0 34" fill="none" stroke="#8B7FF0" stroke-width="4.500" stroke-linecap="round"/>
<path d="M23 21a14 14 0 0 0 0 20M41 21a14 14 0 0 1 0 20" fill="none" stroke="{K}" stroke-width="9" stroke-linecap="round"/><path d="M23 21a14 14 0 0 0 0 20M41 21a14 14 0 0 1 0 20" fill="none" stroke="#5B4BD6" stroke-width="4.500" stroke-linecap="round"/>
<circle cx="32" cy="31" r="8.500" fill="#F59E3A" {S()}/><path d="M32 22.500a8.500 8.500 0 0 1 0 17z" fill="#E07B12" opacity=".8"/><circle cx="29" cy="28" r="2" fill="#fff" opacity=".9"/>'''
