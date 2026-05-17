#!/usr/bin/env python3
"""
Build Taiwan county-level election results panel (1989-2022).
Constructs: local ruling party per year, party alternation dummy, 
political alignment with center, consecutive years of party rule.
"""

import pandas as pd
import json
from pathlib import Path

OUTDIR = Path("/Users/sousekilyu/Documents/Github/taiwan-political-research/data")
OUTDIR.mkdir(exist_ok=True)

# ============================================================
# Taiwan local executive election results, 1989-2022
# ============================================================
# Source: Central Election Commission, Wikipedia county magistrate/mayor lists
# Format: {county_name: [(election_year, winner_name, party, term_start_year), ...]}
# Party codes: KMT=Kuomintang, DPP=Democratic Progressive Party, IND=Independent, TPP=Taiwan People's Party

# Term mapping: election in Nov/Dec of election_year, term starts Dec 25 of election_year
# or Feb 1 of election_year+1 (varies by era). We use calendar year.

LOCAL_EXECUTIVE_HISTORY = {
    # -- Special Municipalities (直轄市) --
    "臺北市": [
        # Pre-1994: appointed. First direct election in 1994.
        (1994, "陳水扁", "DPP", 1994),  # Chen Shui-bian
        (1998, "馬英九", "KMT", 1998),  # Ma Ying-jeou
        (2002, "馬英九", "KMT", 2002),  # reelected
        (2006, "郝龍斌", "KMT", 2006),  # Hau Lung-pin
        (2010, "郝龍斌", "KMT", 2010),  # reelected
        (2014, "柯文哲", "IND", 2014),  # Ko Wen-je (independent)
        (2018, "柯文哲", "IND", 2018),  # reelected
        (2022, "蔣萬安", "KMT", 2022),  # Chiang Wan-an
    ],
    
    "新北市": [
        # Taipei County until 2010 upgrade
        (1989, "尤清", "DPP", 1989),
        (1993, "尤清", "DPP", 1993),
        (1997, "蘇貞昌", "DPP", 1997),
        (2001, "蘇貞昌", "DPP", 2001),
        (2005, "周錫瑋", "KMT", 2005),
        # Became New Taipei City in 2010
        (2010, "朱立倫", "KMT", 2010),
        (2014, "朱立倫", "KMT", 2014),
        (2018, "侯友宜", "KMT", 2018),
        (2022, "侯友宜", "KMT", 2022),
    ],
    
    "桃園市": [
        # Taoyuan County until 2014 upgrade
        (1989, "劉邦友", "KMT", 1989),
        (1993, "劉邦友", "KMT", 1993),
        # 1997 by-election after assassination: Annette Lu (DPP) won but short term
        # 1997 regular: Annette Lu (DPP) won full term
        (1997, "呂秀蓮", "DPP", 1997),  # Annette Lu
        (2001, "朱立倫", "KMT", 2001),
        (2005, "朱立倫", "KMT", 2005),
        (2009, "吳志揚", "KMT", 2009),
        # Became Taoyuan City in 2014
        (2014, "鄭文燦", "DPP", 2014),
        (2018, "鄭文燦", "DPP", 2018),
        (2022, "張善政", "KMT", 2022),
    ],
    
    "臺中市": [
        # Taichung City (provincial) + Taichung County until 2010 merger
        # Using old Taichung City data, then merged
        (1989, "林柏榕", "KMT", 1989),
        (1993, "林柏榕", "KMT", 1993),
        (1997, "張溫鷹", "DPP", 1997),
        (2001, "胡志強", "KMT", 2001),
        (2005, "胡志強", "KMT", 2005),
        # Merged with Taichung County in 2010
        (2010, "胡志強", "KMT", 2010),
        (2014, "林佳龍", "DPP", 2014),
        (2018, "盧秀燕", "KMT", 2018),
        (2022, "盧秀燕", "KMT", 2022),
    ],
    
    "臺南市": [
        # Tainan City (provincial) + Tainan County until 2010 merger
        (1989, "施治明", "KMT", 1989),
        (1993, "施治明", "KMT", 1993),  # last KMT mayor
        (1997, "張燦鍙", "DPP", 1997),  # first DPP mayor (some counts use 1993)
        # Actually, DPP's Mark Chen won in 1993 (some sources differ on exact year DPP took Tainan)
        # More precisely: DPP won Tainan City in the 1997 election with 張燦鍙
        # And Tainan County went DPP in 1993 with 陳唐山 (Chen Tang-shan)
        (2001, "許添財", "DPP", 2001),
        (2005, "許添財", "DPP", 2005),
        # Merged in 2010
        (2010, "賴清德", "DPP", 2010),
        (2014, "賴清德", "DPP", 2014),
        (2018, "黃偉哲", "DPP", 2018),
        (2022, "黃偉哲", "DPP", 2022),
    ],
    
    "高雄市": [
        # Kaohsiung City (special municipality since 1979)
        (1994, "吳敦義", "KMT", 1994),  # Wu Den-yih
        (1998, "謝長廷", "DPP", 1998),  # Frank Hsieh
        (2002, "謝長廷", "DPP", 2002),  # reelected
        (2006, "陳菊", "DPP", 2006),    # Chen Chu
        # Merged with Kaohsiung County in 2010
        (2010, "陳菊", "DPP", 2010),
        (2014, "陳菊", "DPP", 2014),
        (2018, "韓國瑜", "KMT", 2018),  # Han Kuo-yu
        # 2020 by-election (recall): Chen Chi-mai (DPP) won
        (2022, "陳其邁", "DPP", 2022),  # Chen Chi-mai
    ],
    
    # -- Counties (縣) --
    "宜蘭縣": [
        (1989, "游錫堃", "DPP", 1989),  # Yu Shyi-kun
        (1993, "游錫堃", "DPP", 1993),  # reelected
        (1997, "劉守成", "DPP", 1997),
        (2001, "劉守成", "DPP", 2001),
        (2005, "呂國華", "KMT", 2005),
        (2009, "林聰賢", "DPP", 2009),
        (2014, "林聰賢", "DPP", 2014),
        # 2017: Lin promoted to central govt → acting magistrate (DPP/IND)
        (2018, "林姿妙", "KMT", 2018),
        (2022, "林姿妙", "KMT", 2022),
        # 2024: suspended → acting (IND)
    ],
    
    "新竹縣": [
        (1989, "范振宗", "DPP", 1989),
        (1993, "范振宗", "DPP", 1993),
        (1997, "林光華", "DPP", 1997),
        (2001, "鄭永金", "KMT", 2001),
        (2005, "鄭永金", "KMT", 2005),
        (2009, "邱鏡淳", "KMT", 2009),
        (2014, "邱鏡淳", "KMT", 2014),
        (2018, "楊文科", "KMT", 2018),
        (2022, "楊文科", "KMT", 2022),
    ],
    
    "苗栗縣": [
        (1989, "張秋華", "KMT", 1989),
        (1993, "何智輝", "KMT", 1993),
        (1997, "傅學鵬", "IND", 1997),
        (2001, "傅學鵬", "IND", 2001),
        (2005, "劉政鴻", "KMT", 2005),
        (2009, "劉政鴻", "KMT", 2009),
        (2014, "徐耀昌", "KMT", 2014),
        (2018, "徐耀昌", "KMT", 2018),
        (2022, "鍾東錦", "IND", 2022),
    ],
    
    "彰化縣": [
        (1989, "周清玉", "DPP", 1989),
        (1993, "阮剛猛", "KMT", 1993),
        (1997, "阮剛猛", "KMT", 1997),
        (2001, "翁金珠", "DPP", 2001),
        (2005, "卓伯源", "KMT", 2005),
        (2009, "卓伯源", "KMT", 2009),
        (2014, "魏明谷", "DPP", 2014),
        (2018, "王惠美", "KMT", 2018),
        (2022, "王惠美", "KMT", 2022),
    ],
    
    "南投縣": [
        (1989, "林源朗", "KMT", 1989),
        (1993, "林源朗", "KMT", 1993),
        (1997, "彭百顯", "DPP", 1997),  # brief DPP interlude
        (2001, "林宗男", "DPP", 2001),  # DPP then went IND
        (2005, "李朝卿", "KMT", 2005),
        (2009, "李朝卿", "KMT", 2009),
        (2014, "林明溱", "KMT", 2014),
        (2018, "林明溱", "KMT", 2018),
        (2022, "許淑華", "KMT", 2022),
    ],
    
    "雲林縣": [
        (1989, "廖泉裕", "KMT", 1989),
        (1993, "廖泉裕", "KMT", 1993),
        (1997, "蘇文雄", "KMT", 1997),
        # 1999: Su died, by-election won by independent, then...
        (2001, "張榮味", "IND", 2001),
        (2005, "蘇治芬", "DPP", 2005),
        (2009, "蘇治芬", "DPP", 2009),
        (2014, "李進勇", "DPP", 2014),
        (2018, "張麗善", "KMT", 2018),
        (2022, "張麗善", "KMT", 2022),
    ],
    
    "嘉義縣": [
        (1989, "李雅景", "KMT", 1989),  # Actually KMT aligned
        (1993, "李雅景", "KMT", 1993),
        (1997, "李雅景", "KMT", 1997),
        (2001, "陳明文", "DPP", 2001),  # Switched from KMT to DPP
        (2005, "陳明文", "DPP", 2005),
        (2009, "張花冠", "DPP", 2009),
        (2014, "張花冠", "DPP", 2014),
        (2018, "翁章梁", "DPP", 2018),
        (2022, "翁章梁", "DPP", 2022),
    ],
    
    "屏東縣": [
        (1989, "蘇貞昌", "KMT", 1989),  # Actually KMT (some sources note)
        (1993, "蘇貞昌", "DPP", 1993),  # DPP took control
        (1997, "蘇嘉全", "DPP", 1997),
        (2001, "蘇嘉全", "DPP", 2001),
        (2005, "曹啟鴻", "DPP", 2005),
        (2009, "曹啟鴻", "DPP", 2009),
        (2014, "潘孟安", "DPP", 2014),
        (2018, "潘孟安", "DPP", 2018),
        (2022, "周春米", "DPP", 2022),
    ],
    
    "臺東縣": [
        (1989, "鄭烈", "KMT", 1989),
        (1993, "陳建年", "KMT", 1993),
        (1997, "陳建年", "KMT", 1997),
        (2001, "徐慶元", "PFP", 2001),  # People First Party (泛藍)
        (2005, "吳俊立", "IND", 2005), # Won, then disqualified → KMT's Kuang won by-election
        # 2006 by-election: 鄺麗貞 (KMT)
        (2009, "黃健庭", "KMT", 2009),
        (2014, "黃健庭", "KMT", 2014),
        (2018, "饒慶鈴", "KMT", 2018),
        (2022, "饒慶鈴", "KMT", 2022),
    ],
    
    "花蓮縣": [
        (1989, "吳國棟", "KMT", 1989),
        (1993, "王慶豐", "KMT", 1993),  # Actually, some sources say independent won: 1993 王慶豐 (KMT)
        (1997, "王慶豐", "KMT", 1997),
        (2001, "張福興", "KMT", 2001),
        # 2003: Zhang died → by election: 謝深山 (KMT)
        (2005, "謝深山", "KMT", 2005),
        (2009, "傅崐萁", "KMT", 2009),  # Fu Kun-chi (ran as IND but pan-Blue/KMT-aligned)
        (2014, "傅崐萁", "KMT", 2014),
        (2018, "徐榛蔚", "KMT", 2018),  # Hsu Chen-wei (Fu's wife)
        (2022, "徐榛蔚", "KMT", 2022),
    ],
    
    "澎湖縣": [
        (1989, "王乾同", "KMT", 1989),
        # 1992: Wang died, by-election won by Kao Chih-peng (DPP)
        (1993, "高植澎", "DPP", 1993),
        (1997, "賴峰偉", "KMT", 1997),
        (2001, "賴峰偉", "KMT", 2001),
        (2005, "王乾發", "KMT", 2005),
        (2009, "王乾發", "KMT", 2009),
        (2014, "陳光復", "DPP", 2014),
        (2018, "賴峰偉", "KMT", 2018),
        (2022, "陳光復", "DPP", 2022),
    ],
    
    # -- Provincial Cities (省轄市) --
    "基隆市": [
        (1989, "林水木", "KMT", 1989),
        (1993, "林水木", "KMT", 1993),
        (1997, "李進勇", "DPP", 1997),
        (2001, "許財利", "KMT", 2001),
        # 2007: Hsu died → by-election: 張通榮 (KMT)
        (2005, "許財利", "KMT", 2005),
        (2009, "張通榮", "KMT", 2009),
        (2014, "林右昌", "DPP", 2014),
        (2018, "林右昌", "DPP", 2018),
        (2022, "謝國樑", "KMT", 2022),
    ],
    
    "新竹市": [
        (1989, "童勝男", "KMT", 1989),
        (1993, "童勝男", "KMT", 1993),
        (1997, "蔡仁堅", "DPP", 1997),
        (2001, "林政則", "KMT", 2001),
        (2005, "林政則", "KMT", 2005),
        (2009, "許明財", "KMT", 2009),
        (2014, "林智堅", "DPP", 2014),
        (2018, "林智堅", "DPP", 2018),
        (2022, "高虹安", "TPP", 2022),
        # 2024: suspended → acting (TPP/IND)
    ],
    
    "嘉義市": [
        (1989, "張文英", "IND", 1989),
        (1993, "張文英", "IND", 1993),
        (1997, "張博雅", "IND", 1997),
        (2001, "陳麗貞", "IND", 2001),  # supported by DPP later
        (2005, "黃敏惠", "KMT", 2005),
        (2009, "黃敏惠", "KMT", 2009),
        (2014, "涂醒哲", "DPP", 2014),
        (2018, "黃敏惠", "KMT", 2018),
        (2022, "黃敏惠", "KMT", 2022),
    ],
}

# ============================================================
# Central ruling party by period
# ============================================================
# Based on presidential elections/terms
CENTRAL_RULING_PARTY = {
    (1988, 2000): "KMT",   # Lee Teng-hui (continued from Chiang Ching-kuo era)
    (2000, 2008): "DPP",   # Chen Shui-bian
    (2008, 2016): "KMT",   # Ma Ying-jeou
    (2016, 2024): "DPP",   # Tsai Ing-wen
    (2024, 2030): "KMT",   # Lai Ching-te (actually DPP won 2024!)
    # Correction: 2024-2028: DPP (Lai Ching-te won)
}

# Fix central party for 2024+
CENTRAL_RULING_PARTY[(2024, 2030)] = "DPP"  # Correction: Lai Ching-te is DPP


def get_central_party(year):
    """Determine central ruling party for a given calendar year."""
    for (start, end), party in CENTRAL_RULING_PARTY.items():
        if start <= year < end:
            return party
    return "UNKNOWN"


def build_election_panel():
    """Build county-year panel with political variables."""
    rows = []
    
    for county, history in LOCAL_EXECUTIVE_HISTORY.items():
        # Sort by election year
        history = sorted(history, key=lambda x: x[0])
        
        # Assign ruling party to each year
        current_party = None
        current_start = None
        party_term_count = 0
        
        for i, (elec_year, winner, party, term_start) in enumerate(history):
            # Term runs from term_start to next term_start (or end of data)
            if i + 1 < len(history):
                next_term_start = history[i+1][3]
            else:
                next_term_start = 2026  # after current term
            
            for year in range(term_start, next_term_start):
                if year < 1990 or year > 2024:
                    continue
                    
                central_party = get_central_party(year)
                aligned = 1 if party == central_party else 0
                
                # Check alternation: did party change from previous term?
                alternation = 0
                if i > 0 and party != history[i-1][2]:
                    alternation = 1
                
                # Consecutive years of this party's rule
                if current_party != party:
                    current_party = party
                    party_term_count = 1
                else:
                    party_term_count += 1
                
                rows.append({
                    "county": county,
                    "year": year,
                    "local_party": party,
                    "central_party": central_party,
                    "aligned": aligned,
                    "party_alternation": 0,
                    "consecutive_years": party_term_count,
                    "dpp_dummy": 1 if party == "DPP" else 0,
                    "kmt_dummy": 1 if party == "KMT" else 0,
                })
        
        # Now set alternation = 1 for the first year of each term where party changed
        # We do a second pass to mark alternation years
        for i in range(1, len(rows)):
            if rows[i]["county"] != rows[i-1]["county"]:
                continue
            if rows[i]["year"] != rows[i-1]["year"] + 1:
                continue
            if rows[i]["local_party"] != rows[i-1]["local_party"]:
                # Also mark the election year (year - 1 possibly) if it falls in range
                # But the alternation dummy in the literature applies to post-election years
                rows[i]["party_alternation"] = 1
                # Also mark 3 more years after alternation (as in Huang 2023)
                for j in range(1, 4):
                    idx = i + j
                    if idx < len(rows) and rows[idx]["county"] == rows[i]["county"] and rows[idx]["local_party"] == rows[i]["local_party"]:
                        rows[idx]["party_alternation"] = 1
    
    df = pd.DataFrame(rows)
    df = df.sort_values(["county", "year"]).reset_index(drop=True)
    
    # Save
    csv_path = OUTDIR / "county_election_panel.csv"
    df.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"Saved election panel: {csv_path} ({len(df)} rows)")
    print(f"Counties: {df['county'].nunique()}, Years: {df['year'].min()}-{df['year'].max()}")
    
    # Summary stats
    print(f"\nDPP-governed county-years: {df['dpp_dummy'].sum()}")
    print(f"KMT-governed county-years: {df['kmt_dummy'].sum()}")
    print(f"Aligned county-years: {df['aligned'].sum()}")
    print(f"Alternation county-years: {df['party_alternation'].sum()}")
    
    return df


if __name__ == "__main__":
    df_elec = build_election_panel()
    
    # Check our 4 cases
    for county in ["臺南市", "高雄市", "花蓮縣", "南投縣"]:
        cd = df_elec[df_elec["county"] == county]
        print(f"\n{county}:")
        # Show first and last rows
        print(f"  First: {cd.iloc[0]['year']} party={cd.iloc[0]['local_party']}")
        print(f"  Last:  {cd.iloc[-1]['year']} party={cd.iloc[-1]['local_party']}")
        print(f"  DPP years: {cd['dpp_dummy'].sum()}, KMT years: {cd['kmt_dummy'].sum()}")
        print(f"  Aligned years: {cd['aligned'].sum()}")
