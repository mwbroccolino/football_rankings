#! /usr/bin/env python

import sys
import subprocess

def urlOpen(url):
    command = "curl %s >& tmp.txt" % url
    subprocess.call(command, shell=True)
    url_data = open("tmp.txt", "r").readlines()
    subprocess.call("rm tmp.txt", shell=True)
    return url_data

def get_stat(line):
    stat = line.split(">")[1].split("<")[0]
    if stat.count(","):
        stat_tokens = stat.split(",")
        stat_val = float(stat_tokens[0])*1000 + float(stat_tokens[1])
    else: 
        stat_val = float(stat)
    return stat_val 

def get_projections(pos): 
    #-------------------------------
    # Get the data from fantasy pros
    #-------------------------------
    url = "https://www.fantasypros.com/nfl/projections/%s.php?week=draft" % pos.lower() 
    data = urlOpen(url) 

    #-----------------------
    # Parse the messy return
    #-----------------------
    projections = {}
    for i in range(len(data)):
        line = data[i] 
        if line.count("class=\"player-name\"") and len(line) < 1000: 
            tokens = line.split(">")
            name = tokens[3].split("<")[0].strip() 
            if not pos == "DST":
                team = tokens[4].strip().split(" ")[0].strip() 
                tag = "%s %s %s" % (name, pos, team)
            else:
                tag = "%s %s" % (name, pos)

            stats = {}
            if pos == "QB":
                stats["pass_att"]   = get_stat(data[i+1])
                stats["pass_cmp"]   = get_stat(data[i+2])
                stats["pass_yards"] = get_stat(data[i+3])
                stats["pass_tds"]   = get_stat(data[i+4])
                stats["pass_ints"]  = get_stat(data[i+5])
                stats["rush_att"]   = get_stat(data[i+6])
                stats["rush_yards"] = get_stat(data[i+7])
                stats["rush_tds"]   = get_stat(data[i+8])
                stats["fumbles"]    = get_stat(data[i+9])
            
                stats["pass_icmp"]  = stats["pass_att"] - stats["pass_cmp"] 
            elif pos == "RB":
                stats["rush_att"]   = get_stat(data[i+1])
                stats["rush_yards"] = get_stat(data[i+2])
                stats["rush_tds"]   = get_stat(data[i+3])
                stats["rec"]        = get_stat(data[i+4])
                stats["rec_yards"]  = get_stat(data[i+5])
                stats["rec_tds"]    = get_stat(data[i+6])
                stats["fumbles"]    = get_stat(data[i+7])
            elif pos == "WR":
                stats["rush_att"]   = get_stat(data[i+4])
                stats["rush_yards"] = get_stat(data[i+5])
                stats["rush_tds"]   = get_stat(data[i+6])
                stats["rec"]        = get_stat(data[i+1])
                stats["rec_yards"]  = get_stat(data[i+2])
                stats["rec_tds"]    = get_stat(data[i+3])
                stats["fumbles"]    = get_stat(data[i+7])
            elif pos == "TE":
                stats["rec"]        = get_stat(data[i+1])
                stats["rec_yards"]  = get_stat(data[i+2])
                stats["rec_tds"]    = get_stat(data[i+3])
                stats["fumbles"]    = get_stat(data[i+4])
            elif pos == "DST":
                stats["sack"]    = get_stat(data[i+1])
                stats["int"]     = get_stat(data[i+2])
                stats["fr"]      = get_stat(data[i+3])
                stats["ff"]      = get_stat(data[i+4])
                stats["td"]      = get_stat(data[i+5])
                stats["safety"]  = get_stat(data[i+6])
                stats["pa"]      = get_stat(data[i+7]) / 16.0
                stats["yds_agn"] = get_stat(data[i+8])
            elif pos == "K":
                stats["fg"]   = get_stat(data[i+1])
                stats["fga"]  = get_stat(data[i+2])
                stats["xpts"] = get_stat(data[i+3])
            else:
                print "Unexpected position: %s" % pos
            projections[tag] = stats
    return projections

def score_fantasy_points(projections): 
    # mean 
    mean = 0.0
    cnt = 0 
    for player in projections: 
        mean += projections[player]["fantasy_points"]
        cnt += 1
    mean /= cnt 
    print "Mean = %f" % mean

    # std_dev
    std_dev = 0.0
    for player in projections: 
        std_dev += (projections[player]["fantasy_points"] - mean)**2
    std_dev /= cnt

    print "Std dev = %f" % std_dev

    # score
    for player in projections: 
        projections[player]["score"] = (projections[player]["fantasy_points"] - mean) / std_dev 

    for player in projections: 
        print "%s %f" % (player, projections[player]["score"])

    raw_input() 

def compute_fantasy_points(projections): 
    scoring = {"pass_icmp"  :-.3,
               "pass_cmp"   :.5, 
               "pass_yards" :.04,
               "pass_tds"   :6, 
               "pass_ints"  :-4, 
               "rush_att"   :.2,
               "rush_yards" :.1, 
               "rush_tds"   :6, 
               "rec"        :1, 
               "rec_yards"  :.1, 
               "rec_tds"    :6, 
               "fumbles"    :-2, 
               "sack"       :1, 
               "int"        :2, 
               "fr"         :1, 
               "ff"         :1, 
               "td"         :6, 
               "safety"     :2,
               "pa"         :0, 
               "yds_agn"    :0, 
               "fg"         :3,
               "fga"        :-1, 
               "xpts"       :1}

    #---------------------------------
    # Apply the scoring to the players
    #---------------------------------
    for player in projections:
        player_stats = projections[player] 
        player_stats["fantasy_points"] = 0.0
        for key in player_stats.keys():
            if key in [ "fantasy_points", "pass_att"]: continue 
            player_stats["fantasy_points"] += float(scoring[key])*float(player_stats[key])
   

        if pos == "DST":
            if player_stats["pa"] < 7:
                player_stats["fantasy_points"] += 8*16
            elif player_stats["pa"] < 14:
                player_stats["fantasy_points"] += 6*16
            elif player_stats["pa"] < 22:
                player_stats["fantasy_points"] += 2*16
            elif player_stats["pa"] < 28:
                player_stats["fantasy_points"] += -2*16
            elif player_stats["pa"] < 35:
                player_stats["fantasy_points"] += -4*16
            elif player_stats["pa"] < 45:
                player_stats["fantasy_points"] += -8*16
            else: # more than 45
                player_stats["fantasy_points"] += -16*16
    
if __name__ == "__main__":
    #---------------------------------------------
    # Get the latest projections from fantasy pros
    #---------------------------------------------
    positions = ["QB", "RB", "WR", "TE", "DST", "K"]
    projections = {}

    for pos in positions:
        projections[pos] = get_projections(pos)

    #-----------------------------------------------
    # Compute the fantasy points for the projections
    #-----------------------------------------------
    for pos in positions: 
        compute_fantasy_points(projections[pos])

    #-----------------
    # Score the points
    #-----------------
    for pos in positions: 
        score_fantasy_points(projections[pos])
