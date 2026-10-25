from fcdetail import D, S, SH, K
D['Code / API'] = f'''
<ellipse cx="32" cy="60" rx="26" ry="3" {SH}/>
<rect x="3" y="7" width="58" height="48" rx="9" fill="#1E293B" {S()}/>
<path d="M44 7h8a9 9 0 0 1 9 9v30a9 9 0 0 1-9 9h-12z" fill="#0F172A" opacity=".55"/>
<rect x="3" y="7" width="58" height="48" rx="9" fill="none" {S()}/>
<path d="M24 22l-9 9 9 9M40 22l9 9-9 9" fill="none" stroke="#7DD3CB" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M35 19l-6 24" stroke="#F59E3A" stroke-width="4.5" stroke-linecap="round"/>
<path d="M9 13c3-3 8-4 14-4" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".4"/>'''
D['Terminal'] = f'''
<ellipse cx="32" cy="60" rx="26" ry="3" {SH}/>
<rect x="3" y="7" width="58" height="48" rx="8" fill="#0F172A" {S()}/>
<path d="M3 15a8 8 0 0 1 8-8h42a8 8 0 0 1 8 8v4H3z" fill="#334155" {S()}/>
<circle cx="11" cy="13" r="2.2" fill="#D92D20"/><circle cx="18" cy="13" r="2.2" fill="#F59E3A"/><circle cx="25" cy="13" r="2.2" fill="#15803D"/>
<path d="M12 28l9 7-9 7" fill="none" stroke="#7DD3CB" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M27 43h16" stroke="#fff" stroke-width="4.5" stroke-linecap="round"/><rect x="46" y="38" width="6" height="10" fill="#7DD3CB"/>
<path d="M30 28h20" stroke="#94A3B8" stroke-width="3" stroke-linecap="round" opacity=".8"/>'''
D['Lock'] = f'''
<ellipse cx="32" cy="60" rx="20" ry="3" {SH}/>
<path d="M17 29V21a15 15 0 0 1 30 0v8" fill="none" stroke="{K}" stroke-width="9" stroke-linecap="round"/>
<path d="M17 29V21a15 15 0 0 1 30 0v8" fill="none" stroke="#CBD5E1" stroke-width="4.5" stroke-linecap="round"/>
<rect x="8" y="28" width="48" height="31" rx="8" fill="#F59E3A" {S()}/>
<path d="M42 28h6a8 8 0 0 1 8 8v15a8 8 0 0 1-8 8H38z" fill="#E07B12" opacity=".85"/><rect x="8" y="28" width="48" height="31" rx="8" fill="none" {S()}/>
<circle cx="32" cy="41" r="5" fill="#0F172A"/><path d="M32 41v9" stroke="#0F172A" stroke-width="4.5" stroke-linecap="round"/>
<path d="M14 34c2-3 5-4 9-4" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".8"/>'''
D['Key'] = f'''
<ellipse cx="32" cy="60" rx="26" ry="3" {SH}/>
<g transform="rotate(-35 32 31)">
<rect x="26" y="25" width="36" height="12" rx="4" fill="#FFC970" {S()}/>
<path d="M46 37v8h6v-8M54 37v6h5v-6" fill="#FFC970" {S()}/>
<circle cx="15" cy="31" r="13" fill="#F59E3A" {S()}/><path d="M15 18a13 13 0 0 1 0 26z" fill="#E07B12" opacity=".8"/><circle cx="15" cy="31" r="13" fill="none" {S()}/>
<circle cx="15" cy="31" r="5" fill="#FFFFFF" {S('stroke-width="2.2"')}/>
<path d="M32 28h20" stroke="#fff" stroke-width="2.5" stroke-linecap="round" opacity=".8"/></g>
<circle cx="53" cy="10" r="2.5" fill="#7DD3CB"/><path d="M8 52l3 3M11 52l-3 3" stroke="#5B4BD6" stroke-width="2.5" stroke-linecap="round"/>'''
D['Security'] = f'''
<ellipse cx="32" cy="60" rx="20" ry="3" {SH}/>
<path d="M32 3l24 9v18c0 15-10 25-24 30C18 55 8 45 8 30V12z" fill="#DCF5E1" {S()}/>
<path d="M32 3l24 9v18c0 15-10 25-24 30z" fill="#B5EBC1" opacity=".8"/>
<path d="M32 3l24 9v18c0 15-10 25-24 30C18 55 8 45 8 30V12z" fill="none" {S()}/>
<path d="M32 11l16 6v12c0 10-6 17-16 21-10-4-16-11-16-21V17z" fill="#15803D" {S('stroke-width="2"')}/>
<path d="M24 31l6 6 11-12" fill="none" stroke="#fff" stroke-width="5.5" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M13 16c3-3 7-5 12-6" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".8"/>'''
D['Queue'] = f'''
<ellipse cx="32" cy="60" rx="28" ry="3" {SH}/>
<rect x="2" y="22" width="60" height="30" rx="7" fill="#E2E8F0" {S()}/>
<path d="M2 44h60v1a7 7 0 0 1-7 7H9a7 7 0 0 1-7-7z" fill="#CBD5E1"/><rect x="2" y="22" width="60" height="30" rx="7" fill="none" {S()}/>
<rect x="7" y="16" width="14" height="30" rx="3.5" fill="#DCEEFB" {S()}/><rect x="25" y="12" width="14" height="34" rx="3.5" fill="#DCF5E1" {S()}/><rect x="43" y="19" width="14" height="27" rx="3.5" fill="#FFF1DD" {S()}/>
<path d="M11 22h6M29 18h6M47 25h6" stroke="{K}" stroke-width="2.2" stroke-linecap="round"/>
<circle cx="14" cy="37" r="2.4" fill="#1D4ED8"/><circle cx="32" cy="37" r="2.4" fill="#15803D"/><circle cx="50" cy="37" r="2.4" fill="#F59E3A"/>
<path d="M44 52l6-5-6-5" fill="none" stroke="#1D4ED8" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" opacity="0"/>'''
D['Email'] = f'''
<ellipse cx="32" cy="60" rx="26" ry="3" {SH}/>
<rect x="3" y="12" width="58" height="42" rx="8" fill="#FFFFFF" {S()}/>
<path d="M45 12h8a8 8 0 0 1 8 8v26a8 8 0 0 1-8 8H36z" fill="#E2E8F0" opacity=".7"/>
<path d="M5 18l27 21L59 18" fill="#DCEEFB" {S()}/>
<rect x="3" y="12" width="58" height="42" rx="8" fill="none" {S()}/>
<path d="M5 52l19-18M59 52L40 34" fill="none" stroke="{K}" stroke-width="2" stroke-linecap="round" opacity=".5"/>
<circle cx="55" cy="13" r="8.5" fill="#D92D20" stroke="{K}" stroke-width="2.5"/><text x="55" y="17" text-anchor="middle" font-family="Inter, sans-serif" font-size="11" font-weight="800" fill="#fff">1</text>'''
D['Chat'] = f'''
<ellipse cx="32" cy="61" rx="26" ry="2.6" {SH}/>
<path d="M22 24h33a6 6 0 0 1 6 6v17a6 6 0 0 1-6 6H48v8l-10-8H22a6 6 0 0 1-6-6V30a6 6 0 0 1 6-6z" fill="#E6E3FB" {S()}/>
<path d="M52 24a6 6 0 0 1 9 6v17a6 6 0 0 1-6 6h-7v8l-4-3z" fill="#CFC8F7" opacity=".8"/>
<path d="M22 24h33a6 6 0 0 1 6 6v17a6 6 0 0 1-6 6H48v8l-10-8H22a6 6 0 0 1-6-6V30a6 6 0 0 1 6-6z" fill="none" {S()}/>
<path d="M25 34h24M25 42h14" stroke="#5B4BD6" stroke-width="3.2" stroke-linecap="round"/>
<path d="M9 4h33a6 6 0 0 1 6 6v10a6 6 0 0 1-6 6H27l-9 7v-7H9a6 6 0 0 1-6-6V10a6 6 0 0 1 6-6z" fill="#DCEEFB" {S()}/>
<circle cx="15" cy="15" r="2.4" fill="{K}"/><circle cx="26" cy="15" r="2.4" fill="{K}"/><circle cx="37" cy="15" r="2.4" fill="{K}"/>'''
D['Schedule'] = f'''
<ellipse cx="32" cy="60" rx="20" ry="3" {SH}/>
<circle cx="32" cy="32" r="27" fill="#FFFFFF" {S()}/>
<path d="M32 5a27 27 0 0 1 0 54 27 27 0 0 0 0-54z" fill="#E2E8F0" opacity=".8"/>
<circle cx="32" cy="32" r="27" fill="none" {S()}/>
<circle cx="32" cy="32" r="21" fill="#DCEEFB" stroke="{K}" stroke-width="2"/>
<path d="M32 14v3M32 47v3M14 32h3M47 32h3" stroke="{K}" stroke-width="2.5" stroke-linecap="round"/>
<path d="M32 32V19" stroke="{K}" stroke-width="4" stroke-linecap="round"/><path d="M32 32l9 6" stroke="#D92D20" stroke-width="3.5" stroke-linecap="round"/><circle cx="32" cy="32" r="3" fill="{K}"/>
<path d="M13 22c2-4 5-7 9-9" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".9"/>
<rect x="26" y="1" width="12" height="5" rx="2" fill="#F59E3A" stroke="{K}" stroke-width="2"/>'''
D['Pipeline'] = f'''
<ellipse cx="32" cy="60" rx="28" ry="3" {SH}/>
<rect x="2" y="14" width="18" height="18" rx="5" fill="#DCEEFB" {S()}/><rect x="23" y="14" width="18" height="18" rx="5" fill="#DCF5E1" {S()}/><rect x="44" y="14" width="18" height="18" rx="5" fill="#FFF1DD" {S()}/>
<path d="M20 23h3M41 23h3" stroke="{K}" stroke-width="2.5"/>
<path d="M7 21l4-3 4 3v6H7zM27 23l3 3 5-6M50 28l4-9 4 9z" fill="none" stroke="{K}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" opacity="0"/>
<path d="M6 23l5-4 5 4-5 4z" fill="#1D4ED8" stroke="{K}" stroke-width="1.8" stroke-linejoin="round"/>
<path d="M27 23l3.5 3.5L37 19" fill="none" stroke="#15803D" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M53 28v-9M49 23l4-4 4 4" fill="none" stroke="#F59E3A" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
<rect x="2" y="42" width="60" height="12" rx="6" fill="#E2E8F0" {S()}/><rect x="2" y="42" width="40" height="12" rx="6" fill="#15803D" {S()}/>
<path d="M8 46h22" stroke="#fff" stroke-width="2.5" stroke-linecap="round" opacity=".7"/>
<path d="M11 36v6M32 36v6M53 36v6" stroke="{K}" stroke-width="2" stroke-linecap="round" opacity=".5"/>'''
