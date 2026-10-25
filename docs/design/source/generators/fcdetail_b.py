from fcdetail import D, S, SH, K
D['Cache'] = f'''
<ellipse cx="32" cy="60" rx="22" ry="3" {SH}/>
<path d="M18 3v7M32 3v7M46 3v7M18 54v7M32 54v7M46 54v7M3 18h7M3 32h7M3 46h7M54 18h7M54 32h7M54 46h7" stroke="{K}" stroke-width="2.5" stroke-linecap="round"/>
<rect x="9" y="9" width="46" height="46" rx="10" fill="#FFF1DD" {S()}/><path d="M43 9h2a10 10 0 0 1 10 10v26a10 10 0 0 1-10 10h-8z" fill="#FFE2B0" opacity=".9"/><rect x="9" y="9" width="46" height="46" rx="10" fill="none" {S()}/>
<path d="M36 14L20 34h10l-4 16 18-24H33z" fill="#F59E3A" stroke="{K}" stroke-width="2.5" stroke-linejoin="round"/>
<path d="M15 18c2-3 4-4 7-5" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".8"/>'''
D['File'] = f'''
<ellipse cx="32" cy="60" rx="20" ry="3" {SH}/>
<path d="M12 3h27l15 15v41H12z" fill="#FFFFFF" {S()}/><path d="M44 3h-5l15 15v41H44z" fill="#E2E8F0" opacity=".8"/><path d="M12 3h27l15 15v41H12z" fill="none" {S()}/>
<path d="M39 3v15h15z" fill="#DCF5E1" {S()}/>
<path d="M19 28h22M19 36h26M19 44h16" stroke="#94A3B8" stroke-width="3.2" stroke-linecap="round"/>
<rect x="19" y="49" width="12" height="6" rx="3" fill="#1D4ED8"/>
<path d="M16 9l8-1" stroke="#fff" stroke-width="2" stroke-linecap="round"/>'''
D['Folder'] = f'''
<ellipse cx="32" cy="60" rx="26" ry="3" {SH}/>
<path d="M4 14a4 4 0 0 1 4-4h16l6 7h26a4 4 0 0 1 4 4v33a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4z" fill="#FFC970" {S()}/>
<rect x="11" y="19" width="40" height="22" rx="2" fill="#FFFFFF" {S('stroke-width="2.2"')}/><path d="M17 26h22M17 32h14" stroke="#94A3B8" stroke-width="2.6" stroke-linecap="round"/>
<path d="M4 28a4 4 0 0 1 4-4h48a4 4 0 0 1 4 4v28a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4z" fill="#FFE2B0" {S()}/>
<path d="M44 24h12a4 4 0 0 1 4 4v28a4 4 0 0 1-4 4h-6z" fill="#F7C77E" opacity=".7"/>
<path d="M9 32c4-1 9-1 14-1" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".8"/>'''
D['Bucket'] = f'''
<ellipse cx="32" cy="60" rx="22" ry="3" {SH}/>
<path d="M12 22C16 4 48 4 52 22" fill="none" {S('stroke-width="3"')}/>
<path d="M8 20l6 36c1 3 8 5 18 5s17-2 18-5l6-36z" fill="#DCEEFB" {S()}/>
<path d="M47 20h9l-6 36c-.5 2-3 3.5-7 4.5z" fill="#B8D6F2" opacity=".85"/>
<path d="M10 33c5 4 10 4 14 1s9-3 14 0 9 3 15 0l1-5H10z" fill="#1D4ED8" opacity=".85"/>
<path d="M8 20l6 36c1 3 8 5 18 5s17-2 18-5l6-36" fill="none" {S()}/>
<ellipse cx="32" cy="20" rx="24" ry="7.5" fill="#1D4ED8" {S()}/><ellipse cx="32" cy="18.5" rx="14" ry="3" fill="#fff" opacity=".35"/>
<path d="M15 34l3 17" stroke="#fff" stroke-width="2.5" stroke-linecap="round" opacity=".6"/>'''
D['Cloud'] = f'''
<ellipse cx="32" cy="58" rx="24" ry="3" {SH}/>
<path d="M17 48a13 13 0 0 1-2-25.8A18 18 0 0 1 49 24a12 12 0 0 1-2 24z" fill="#DCEEFB" {S()}/>
<path d="M49 24a12 12 0 0 1-2 24H34c8-3 12-10 10-20 2-4 4-4 5-4z" fill="#B8D6F2" opacity=".85"/>
<path d="M17 48a13 13 0 0 1-2-25.8A18 18 0 0 1 49 24a12 12 0 0 1-2 24z" fill="none" {S()}/>
<path d="M18 22c3-6 9-9 15-8" fill="none" stroke="#fff" stroke-width="3.2" stroke-linecap="round" opacity=".85"/>
<path d="M32 42V28M25 34l7-7 7 7" fill="none" stroke="#1D4ED8" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'''
D['Globe'] = f'''
<ellipse cx="32" cy="60" rx="18" ry="3" {SH}/>
<circle cx="32" cy="31" r="26" fill="#D3F3EF" {S()}/>
<path d="M14 18c4-3 8-3 11-1s1 6 4 8-1 8-5 8-7-5-9-7-3-6-1-8z" fill="#15803D" stroke="{K}" stroke-width="2" stroke-linejoin="round"/>
<path d="M38 12c5 0 10 3 13 8-2 3-5 2-7 5s0 6-3 7-5-3-4-7 3-3 2-6-3-4-1-7z" fill="#15803D" stroke="{K}" stroke-width="2" stroke-linejoin="round"/>
<path d="M32 5a26 26 0 0 1 0 52 26 26 0 0 0 0-52z" fill="#7DD3CB" opacity=".45"/>
<ellipse cx="32" cy="31" rx="11" ry="26" fill="none" stroke="{K}" stroke-width="1.6" opacity=".35"/>
<circle cx="32" cy="31" r="26" fill="none" {S()}/>
<path d="M15 20c3-6 8-10 14-12" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".8"/>'''
D['Firewall'] = f'''
<ellipse cx="32" cy="60" rx="28" ry="3" {SH}/>
<path d="M33 3c1 6 8 9 8 17 0 3-1 5-3 7 0-4-2-6-4-8 1 4-2 7-4 9-2-2-3-4-2-7-4 3-6 7-5 11h-3c-2-9 4-14 8-18 3-3 5-6 5-11z" fill="#F59E3A" stroke="{K}" stroke-width="2.2" stroke-linejoin="round"/>
<path d="M33 12c1 4 5 6 5 11-1-2-3-3-4-4 0 3-2 5-3 6-1-2-1-4 0-6z" fill="#FFE2B0"/>
<rect x="3" y="26" width="58" height="32" rx="2" fill="#FDE4E4" {S()}/>
<path d="M3 37h58M3 48h58M19 26v11M42 26v11M11 37v11M30 37v11M50 37v11M19 48v10M42 48v10" stroke="{K}" stroke-width="2.2"/>
<rect x="3" y="26" width="58" height="32" rx="2" fill="none" {S()}/>
<path d="M56 38v20h-6V38z" fill="#D92D20" opacity=".25"/>
<path d="M6 30h10" stroke="#fff" stroke-width="2.5" stroke-linecap="round" opacity=".9"/>'''
D['CDN'] = f'''
<ellipse cx="32" cy="60" rx="24" ry="3" {SH}/>
<path d="M11 11l11 11M53 11L42 22M11 51l11-11M53 51L42 40" stroke="{K}" stroke-width="2.5" stroke-linecap="round"/>
<circle cx="32" cy="31" r="17" fill="#D3F3EF" {S()}/>
<path d="M32 14a17 17 0 0 1 0 34 17 17 0 0 0 0-34z" fill="#7DD3CB" opacity=".5"/>
<path d="M15 31h34M32 14c6 7 6 27 0 34M32 14c-6 7-6 27 0 34" fill="none" stroke="{K}" stroke-width="1.8" opacity=".6"/>
<circle cx="32" cy="31" r="17" fill="none" {S()}/>
<circle cx="8" cy="8" r="6" fill="#F59E3A" {S()}/><circle cx="56" cy="8" r="6" fill="#F59E3A" {S()}/><circle cx="8" cy="54" r="6" fill="#F59E3A" {S()}/><circle cx="56" cy="54" r="6" fill="#F59E3A" {S()}/>
<path d="M5.5 6l2-1.5M53.5 6l2-1.5" stroke="#fff" stroke-width="2" stroke-linecap="round" opacity=".8"/>'''
D['Browser'] = f'''
<ellipse cx="32" cy="60" rx="26" ry="3" {SH}/>
<rect x="3" y="7" width="58" height="48" rx="7" fill="#FFFFFF" {S()}/>
<path d="M3 14a7 7 0 0 1 7-7h44a7 7 0 0 1 7 7v8H3z" fill="#DCEEFB" {S()}/>
<circle cx="11" cy="14.5" r="2.2" fill="#D92D20"/><circle cx="18" cy="14.5" r="2.2" fill="#F59E3A"/><circle cx="25" cy="14.5" r="2.2" fill="#15803D"/>
<rect x="32" y="11.5" width="23" height="6" rx="3" fill="#FFFFFF" stroke="{K}" stroke-width="1.6"/>
<rect x="9" y="28" width="22" height="20" rx="3" fill="#FFF1DD" {S('stroke-width="2"')}/><circle cx="16" cy="35" r="3" fill="#F59E3A"/><path d="M11 45l7-6 5 4 6-5" fill="none" stroke="#15803D" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M36 30h19M36 37h15M36 44h19" stroke="#94A3B8" stroke-width="3.2" stroke-linecap="round"/>
<path d="M50 7h4a7 7 0 0 1 7 7v34a7 7 0 0 1-7 7h-6z" fill="#E2E8F0" opacity=".5"/>'''
D['Laptop'] = f'''
<ellipse cx="32" cy="61" rx="29" ry="2.6" {SH}/>
<rect x="9" y="8" width="46" height="34" rx="5" fill="#DCEEFB" {S()}/>
<rect x="14" y="13" width="36" height="24" rx="2" fill="#0F172A"/>
<path d="M18 20l5 4-5 4M27 29h9" fill="none" stroke="#7DD3CB" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M30 14l8-1-8 24h-8z" fill="#fff" opacity=".12"/>
<path d="M3 44h58l-3 10a4 4 0 0 1-4 3H10a4 4 0 0 1-4-3z" fill="#CBD5E1" {S()}/>
<path d="M26 44v3h12v-3" fill="#94A3B8" stroke="{K}" stroke-width="2" stroke-linejoin="round"/>
<path d="M44 44h14l-2 8a4 4 0 0 1-4 3h-12z" fill="#94A3B8" opacity=".45"/>'''
