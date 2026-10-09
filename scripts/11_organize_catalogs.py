"""Organiza a ORC Asset Library em catalogos (pastas) e cria 2 versoes:
   - ORC_AssetLibrary_NoProps.blend   (Characters + Enemies + Weapons + VFX)
   - ORC_AssetLibrary_PropsOnly.blend (somente Props)
"""
import bpy, os, re, uuid, sys

# pasta da biblioteca (configuravel: 1o argumento apos -- , ou env ORC_LIBDIR)
_argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
LIBDIR = _argv[0] if _argv else (os.environ.get("ORC_LIBDIR") or r"C:\ORC-COMPLETO\ORC-Asset-Library")
MASTER = os.path.join(LIBDIR, "ORC_AssetLibrary.blend")

def U(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "orc-asset-library/" + name))

# ---- estrutura de catalogos (aninhados) ----
CATALOGS = [
    "Characters", "Characters/Playable", "Characters/NPCs",
    "Enemies", "Enemies/Zombies", "Enemies/BOWs and Monsters",
    "Enemies/Enemy Soldiers", "Enemies/Gore",
    "Weapons", "VFX",
    "Props", "Props/Vehicles", "Props/Doors and Gates", "Props/Lights",
    "Props/Signs and Decals", "Props/Furniture", "Props/Containers",
    "Props/Machinery and Tech", "Props/Medical and Lab", "Props/Nature and Terrain",
    "Props/Debris and Gore", "Props/Architecture", "Props/Outdoor and Street",
    "Props/Props and Items", "Props/Misc",
]

# ---- personagens: jogaveis/NPC vs inimigos ----
PLAYABLE = {"adawong","beltway","beltwayv1","berthamale","berthamalev1","carlosolveria",
    "carlosoliveria","claireredfield","deeay","foureyes","foureyesv1","harley","hunk",
    "jillvalentine","leon","lonewolf","lupo","lupov1","nicholaiginovaef","partygirl",
    "sherrybirkin","shona","spook","spookv1","tweed","uss","ussleader","vector","vectorv1","willow"}
GORE = {"ch_claws","fr_armfull_l","fr_armfull_r","fr_armlower_l","fr_armlower_l_sm",
    "fr_armlower_r","fr_armlower_r_sm","fr_armupper_l","fr_armupper_r","fr_leg_l","fr_leg_r",
    "fr_torso_bottom","fr_torso_top","neck_01","femonster_organ","femonster_skeleton","femonster_skin"}
ZOMBIES_PRE = ("zb_", "zombiedog", "crimsonhead", "licker", "hunter", "elitehunter")
SOLDIERS = {"specops","specops2","specops3","specops4","specops5","specops6","specops_wound","ubcs","ubcszombie"}

# ---- props: classificacao (tokens) ----
PROP_RULES = [
 ("Props/Vehicles",  ["car","bus","truck","van","ambulance","heli","helicopter","boat","motorcycle","motorbike","bike","train","tank","suv","sedan","wagon","pontiac","honda","forklift","tractor","tram","subway","monorail","trailer","carriage","crane","pickup","taxi","coupe","veh","firetruck","tires","tire","shopping_cart","stroller","tricycle","wheelbarrow"]),
 ("Props/Doors and Gates", ["door","gate","hatch","barricade","chainlink","chainlinkfence","chainlinkgate","shutter","turnstile","accordiangate","airlock","garage","fence","railing","barrier","portcullis","parkadedoor","parkgate","grate"]),
 ("Props/Lights",    ["light","lamp","lantern","sconce","neon","fluorescent","chandelier","spotlight","searchlight","streetlight","floodlight","beacon","bulb","lightbar","torch","siren"]),
 ("Props/Signs and Decals", ["sign","sgn","billboard","poster","decal","painting","graffiti","banner","plaque","logo","label","sticker","advert","notice","mural","flag","stagstreet","bulletin_board","white_board","family_pictures","newspaperdispenser","maps"]),
 ("Props/Furniture", ["chair","table","desk","bed","cabinet","shelf","shelves","bench","sofa","couch","locker","drawer","dresser","stool","wardrobe","bookcase","cupboard","bunk","crib","ottoman","armoire","hutch","nightstand","vanity","mattress","filecabinet","cart","dolly"]),
 ("Props/Containers",["box","crate","barrel","drum","can","bin","case","container","containera","containerb","containerc","pallet","pallette","palete","pallettes","tote","basket","bucket","chest","trunk","ammo","briefcase","suitcase","cargo","coffin","safe","urn","vial","canister","jerrycan","feedbags","plywood","pail"]),
 ("Props/Machinery and Tech", ["machine","machinery","computer","terminal","generator","powergenerator","pipe","pipes","pipesbent","pipesstraight","pipesdrain","lrgpipe","vent","roofvent","wallvent","circuit","circut","monitor","monitors","elevator","engine","motor","pump","fan","turbine","conveyor","cctv","camera","securitycamera","server","console","panel","breaker","switch","valve","meter","gasmeter","antenna","satellite","transformer","boiler","compressor","hydraulic","robot","press","lathe","drill","airduct","duct","gauge","dial","clock","wires","hanging_wires","wireswall","air_conditioner","aptbuzzer","intercom","hunterpod","hunter_pod","incinerator","inc_","steel_cooler","chiller","powerpole","electrical_towers","tower_electrical","laserpad","machines","railyard","vacuum","funnel","cement_mixer","conduit","radar","extinguisher","water_heater","watercooler","ind_aircon","laundry_chute","band_saw","ladder"]),
 ("Props/Medical and Lab", ["lab","hospital","medical","syringe","biotech","fume","autopsy","operating","surgery","specimen","beaker","flask","microscope","incubator","centrifuge","cage","stretcher","wheelchair","gurney","mortuary","morgue","pharma","clinic","ward","xray","infirmary","decontamination","medicinecups","infant","drugs","urinal","washroom","tub_biowaste","instruments","petri","vat","ladle"]),
 ("Props/Nature and Terrain", ["tree","bush","grass","terrain","rock","boulder","plant","flower","leaf","leaves","ivy","vine","moss","dirt","sand","snow","puddle","puddles","cliff","hill","mound","stump","log","root","fern","hedge","shrub","garden","branch","magma","stones","planter","weeds","dry_reeds","reeds","ants","bullrush"]),
 ("Props/Debris and Gore", ["debris","rubble","broken","glass","chunk","trash","garbage","wreck","scrap","junk","ash","dust","shard","fragment","remains","corpse","blood","bloodtarp","stain","spill","pile","heap","refuse","litter","ruin","dead","guts","gutspile","gore","destroy","spawn","body_dead","body_sheet","bodybag","hole_collapsed"]),
 ("Props/Architecture", ["wall","corrugatedwall","floor","ceiling","roof","column","columnsmall","arch","dome","stair","stairs","steps","balcony","corridor","hall","hallway","room","building","bld","bridge","ramp","platform","atrium","lobby","concourse","passage","tunnel","maintun","foundation","pillar","beam","girder","molding","trim","facade","parapet","balustrade","landing","mezzanine","walkway","catwalk","porch","awning","canopy","alcove","niche","fireplace","chimney","skylight","window","doorway","threshold","tile","brick","concrete","pavement","sidewalk","curb","asphalt","manhole","drain","sewer","swr","cityhall","lonsdale","warehouse","deadfactory","lc","foundry","stagalleybld","stag","iron","crypt","parkade","rpd","rpdinterior","scaffold","scaffolding","underground","core","coreshaft","lowercore","southwing","so0","so_","mp_hallway","n_stairwell","attic","auditorium","diner","theater","safehouse","policestation","police_station","rc_hotel","kendo","junction","helipad","smokestack","watertower","large_warehouse","fire_escape","factory","dfactory","dt","birkinroom","birkin_battlezone","programlab","hut","spt_arena","spt","hospwindowsill","highrises","sniperstreet","bow_reception","front_reception","divider","cubicle","counter","boiler_room","yard","blockers","boarded","os_","blocker","alleyblockwall","catacombs_wood_support","podium","cement_stack","woodstack","tarp","rail_stopper","railpiece","policestn","so05","tyrant_entrance","maintenance","hole"]),
 ("Props/Outdoor and Street", ["street","road","alley","hydrant","pole","traffic","parking","plaza","park","playground","mailbox","dumpster","dumpsterclean","telephone","phonebooth","shelter","busstop","lamppost","fountain","statue","sculpture","monument","grave","tomb","tombstone","cemet","cemetery","memorial","signpost","courtyard","garbagecan","portapotty","dog_kennel","yard_sandbags","powerpole","railyard","flags_crossed"]),
 ("Props/Props and Items", ["bottle","mug","cup","plate","bowl","food","cake","book","books","paper","document","file","folder","keyboard","mouse","phone","radio","tv","television","tool","wrench","hammer","screwdriver","knife","bullet","grenade","explosive","medkit","bandage","pill","oil","paint","spray","mop","broom","towel","cloth","rug","carpet","curtain","blanket","pillow","watch","mirror","vase","pot","pan","kettle","appliance","fridge","freezer","stove","oven","sink","toilet","shower","bathtub","washer","dryer","microwave","vending","atm","register","coin","card","jar","dish","cutlery","utensil","candle","trophy","award","medal","ball","toy","doll","game","instrument","guitar","piano","ornament","decor","frame","photo","photos","album","tissue","napkin","soap","brush","comb","razor","toothbrush","umbrella","backpack","bag","purse","wallet","helmet","boot","shoe","clothing","clothes","uniform","hat","glove","intel","records","typewriter","tape_recorder","floppy","laptop","film","projector","mannequin","ingots","magazine","pen","plates_party","pressure_cooker","cauldron","altar","holy_water","gargoyle","taxidermy","deer_head","cow_head","tiger","falcon","raccoon","mrcrispy","balloons","balloon","organ","newspaper","mail_parcels","smoke_stack","screen","hologram","core_glow","magazine_rack","counter_cashier","dog_tags","cleaning_supplies","tanks","a_crawl","cc_"]),
]

def toks(n):
    return set(re.findall(r'[a-z]+', n.lower()))

def classify_prop(n):
    T = toks(n); low = n.lower()
    for cat, keys in PROP_RULES:
        for k in keys:
            if "_" in k or len(k) > 4:
                if k in low:
                    return cat
            if k in T:
                return cat
    return "Props/Misc"

def catalog_for(master, name):
    if master == "Weapons":
        return "Weapons"
    if master == "VFX":
        return "VFX"
    if master == "Props":
        return classify_prop(name)
    if master == "Characters":
        if name in GORE:
            return "Enemies/Gore"
        if name in PLAYABLE:
            return "Characters/Playable"
        if name in SOLDIERS:
            return "Enemies/Enemy Soldiers"
        if name.startswith(ZOMBIES_PRE):
            return "Enemies/Zombies"
        return "Enemies/BOWs and Monsters"
    return None

# ================= 1) MASTER: aplicar catalogos =================
bpy.ops.wm.open_mainfile(filepath=MASTER)
from collections import Counter
counts = Counter()
for master in ("Characters", "Weapons", "VFX", "Props"):
    m = bpy.data.collections.get(master)
    if not m:
        continue
    for sub in m.children:
        cat = catalog_for(master, sub.name)
        if cat and sub.asset_data:
            sub.asset_data.catalog_id = U(cat)
            counts[cat] += 1
print("=== MASTER: catalogos ===", flush=True)
for k in CATALOGS:
    if counts.get(k):
        print(f"  {k}: {counts[k]}", flush=True)
print("total:", sum(counts.values()), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=MASTER, compress=True)
print("MASTER SAVED", flush=True)

# ================= 2) escrever cats.txt =================
cats_path = os.path.join(LIBDIR, "blender_assets.cats.txt")
with open(cats_path, "w", encoding="utf-8") as f:
    f.write("# This is an Asset Catalog Definition file for Blender.\n#\n")
    f.write("# Empty lines and lines starting with `#` will be ignored.\n")
    f.write("# The first non-ignored line should be the version indicator.\n")
    f.write('# Other lines are of the format "UUID:catalog/path/for/assets:simple catalog name"\n\n')
    f.write("VERSION 1\n\n")
    for c in CATALOGS:
        simple = c.split("/")[-1]
        f.write(f"{U(c)}:{c}:{simple}\n")
print("CATS.TXT escrito", flush=True)
