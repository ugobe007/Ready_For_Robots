"""
Curated catalog of humanoid robot companies and flagship products.

Used by humanoid discovery to seed ``humanoid_benchmarks`` beyond the original
11-robot seed set. Sources: HEIR 2026, manufacturer sites, trade show lists,
and industry coverage (2024–2026).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.services.humanoid_catalog_cleanup import (
    is_excluded_humanoid_slug,
    is_junk_humanoid_row,
)

# Each entry: name, vendor, optional model_slug, product_url, status, country, specs (partial)
HUMANOID_CATALOG: List[Dict[str, Any]] = [
    # ── Tier 1 — commercially visible ────────────────────────────────────────
    {"name": "Unitree G1", "vendor": "Unitree Robotics", "model_slug": "unitree-g1", "product_url": "https://www.unitree.com/g1", "vendor_url": "https://www.unitree.com", "vendor_name_cn": "宇树科技", "robot_name_cn": "G1人形机器人", "vendor_aliases": "Unitree|宇树科技|Unitree Robotics", "robot_aliases": "Unitree G1|G1人形机器人|G1", "status": "available", "country": "China"},
    {"name": "Unitree H1", "vendor": "Unitree Robotics", "model_slug": "unitree-h1", "product_url": "https://www.unitree.com/h1", "vendor_url": "https://www.unitree.com", "vendor_name_cn": "宇树科技", "robot_name_cn": "H1人形机器人", "vendor_aliases": "Unitree|宇树科技|Unitree Robotics", "robot_aliases": "Unitree H1|H1人形机器人|H1", "status": "available", "country": "China"},
    {"name": "Unitree R1", "vendor": "Unitree Robotics", "model_slug": "unitree-r1", "product_url": "https://www.unitree.com", "vendor_url": "https://www.unitree.com", "vendor_name_cn": "宇树科技", "vendor_aliases": "Unitree|宇树科技|Unitree Robotics", "robot_aliases": "Unitree R1|R1", "status": "pilot", "country": "China"},
    {"name": "Figure 02", "vendor": "Figure AI", "model_slug": "figure-02", "product_url": "https://www.figure.ai", "status": "pilot", "country": "USA"},
    {"name": "Figure 01", "vendor": "Figure AI", "model_slug": "figure-01", "product_url": "https://www.figure.ai", "status": "research", "country": "USA"},
    {"name": "Agility Digit", "vendor": "Agility Robotics", "model_slug": "agility-digit", "product_url": "https://www.agilityrobotics.com/solutions", "status": "available", "country": "USA"},
    {"name": "Tesla Optimus Gen 2", "vendor": "Tesla", "model_slug": "tesla-optimus-gen2", "product_url": "https://www.tesla.com/AI", "status": "pilot", "country": "USA"},
    {"name": "Boston Dynamics Atlas", "vendor": "Boston Dynamics", "model_slug": "boston-dynamics-atlas", "product_url": "https://bostondynamics.com/atlas", "status": "pilot", "country": "USA"},
    {"name": "Apptronik Apollo", "vendor": "Apptronik", "model_slug": "apptronik-apollo", "product_url": "https://apptronik.com/apollo", "status": "pilot", "country": "USA"},
    {"name": "1X NEO", "vendor": "1X Technologies", "model_slug": "1x-neo", "product_url": "https://www.1x.tech/neo", "status": "pilot", "country": "USA"},
    {"name": "1X Eve", "vendor": "1X Technologies", "model_slug": "1x-eve", "product_url": "https://www.1x.tech", "status": "pilot", "country": "Norway"},
    {"name": "Sanctuary Phoenix", "vendor": "Sanctuary AI", "model_slug": "sanctuary-phoenix", "product_url": "https://www.sanctuary.ai", "status": "pilot", "country": "Canada", "specs": {"has_dexterous_hands": True, "finger_count": 5, "autonomy_level": "semi", "has_sdk": True, "has_api": True, "has_estop": True, "force_limited_joints": True, "commercial_deployments": 10, "has_support_sla": True}},
    {"name": "Agibot A2", "vendor": "Agibot (Zhiyuan Robotics)", "model_slug": "agibot-a2", "product_url": "https://agibot.com", "vendor_url": "https://www.agibot.com", "vendor_name_cn": "智元机器人", "robot_name_cn": "远征A2", "vendor_aliases": "AgiBot|智元机器人|Zhiyuan Robotics|Zhiyuan", "robot_aliases": "AgiBot A2|远征A2|Yuanzheng A2", "status": "available", "country": "China"},
    {"name": "Agibot G5", "vendor": "Agibot (Zhiyuan Robotics)", "model_slug": "agibot-g5", "product_url": "https://agibot.com", "vendor_url": "https://www.agibot.com", "vendor_name_cn": "智元机器人", "vendor_aliases": "AgiBot|智元机器人|Zhiyuan Robotics|Zhiyuan", "robot_aliases": "AgiBot G5|Agibot G5|G5", "status": "pilot", "country": "China"},
    {"name": "UBTECH Walker X", "vendor": "UBTECH Robotics", "model_slug": "ubtech-walker-x", "product_url": "https://www.ubtrobot.com/en/", "vendor_url": "https://www.ubtrobot.com", "vendor_name_cn": "优必选", "robot_name_cn": "Walker X", "vendor_aliases": "UBTECH|优必选|UBTECH Robotics|UBTech", "robot_aliases": "Walker X|UBTECH Walker X", "status": "available", "country": "China"},
    {"name": "UBTECH Walker S", "vendor": "UBTECH Robotics", "model_slug": "ubtech-walker-s", "product_url": "https://www.ubtrobot.com/en/", "vendor_url": "https://www.ubtrobot.com", "vendor_name_cn": "优必选", "robot_name_cn": "Walker S", "vendor_aliases": "UBTECH|优必选|UBTECH Robotics|UBTech", "robot_aliases": "Walker S|Walker S1|Walker S2|UBTECH Walker S", "status": "pilot", "country": "China"},
    {"name": "Generalist GEN-1", "vendor": "Generalist AI", "model_slug": "generalist-gen1", "product_url": "https://generalistai.com/", "status": "research", "country": "USA", "specs": {"has_dexterous_hands": True, "finger_count": 5, "can_navigate_rough_terrain": True, "autonomy_level": "semi", "has_estop": True, "force_limited_joints": True, "commercial_deployments": 0}},
    {"name": "Galaxea Kengo", "vendor": "Galaxea Dynamics", "model_slug": "galaxea-kengo", "product_url": "https://humanoid.guide/welcome-kengo/", "vendor_url": "https://galaxea.ai", "vendor_name_cn": "星海图", "vendor_aliases": "Galaxea|Galaxea AI|Galaxea Dynamics|星海图", "robot_aliases": "Galaxea Kengo|Kengo", "status": "research", "country": "China", "specs": {"height_cm": 170, "weight_kg": 65, "has_dexterous_hands": True, "finger_count": 5, "can_climb_stairs": True, "can_navigate_rough_terrain": True, "autonomy_level": "semi", "has_estop": True, "force_limited_joints": True, "has_sdk": True, "has_api": True, "commercial_deployments": 0}},
    {"name": "Foundation Phantom", "vendor": "Foundation Future Industries", "model_slug": "foundation-phantom", "product_url": "https://foundation.bot/", "status": "research", "country": "USA", "specs": {"has_dexterous_hands": True, "finger_count": 5, "can_navigate_rough_terrain": True, "autonomy_level": "semi", "has_estop": True, "force_limited_joints": True, "commercial_deployments": 0}},
    {"name": "High Torque Mini Pi plus", "vendor": "High Torque Robotics", "model_slug": "high-torque-mini-pi-plus", "product_url": "https://www.hightorquerobotics.com/", "vendor_url": "https://www.hightorquerobotics.com", "vendor_name_cn": "本末科技", "vendor_aliases": "High Torque|High Torque Robotics|本末科技", "robot_aliases": "Mini Pi plus|Mini Pi+|MiniPi plus", "status": "available", "country": "China", "specs": {"has_sdk": True, "has_api": True, "has_estop": True, "force_limited_joints": True, "autonomy_level": "research", "commercial_deployments": 10, "height_cm": 90, "weight_kg": 12}},
    {"name": "High Torque Mini Pi", "vendor": "High Torque Robotics", "model_slug": "high-torque-mini-pi", "product_url": "https://www.hightorquerobotics.com/", "vendor_url": "https://www.hightorquerobotics.com", "vendor_name_cn": "本末科技", "vendor_aliases": "High Torque|High Torque Robotics|本末科技", "robot_aliases": "Mini Pi|MiniPi", "status": "available", "country": "China", "specs": {"has_sdk": True, "has_api": True, "has_estop": True, "autonomy_level": "research", "commercial_deployments": 8}},
    {"name": "Andromeda Abi", "vendor": "Andromeda Robotics", "model_slug": "andromeda-abi", "product_url": "https://andromedarobotics.ai/", "status": "pilot", "country": "Australia", "specs": {"has_dexterous_hands": True, "finger_count": 5, "can_navigate_rough_terrain": True, "autonomy_level": "semi", "has_estop": True, "force_limited_joints": True, "has_support_sla": True, "commercial_deployments": 15, "height_cm": 140, "weight_kg": 45}},
    {"name": "Humanoid HMND 01 Alpha Bipedal", "vendor": "Humanoid (SKL Robotics)", "model_slug": "humanoid-hmnd01-alpha-bipedal", "product_url": "https://thehumanoid.ai/", "vendor_url": "https://thehumanoid.ai", "vendor_aliases": "Humanoid|HMND|SKL Robotics|SKL Robotics LTD|thehumanoid", "robot_aliases": "HMND 01|HMND 01 Alpha Bipedal|Alpha Bipedal", "verification_status": "VERIFIED", "status": "pilot", "country": "UK", "specs": {"top_speed_mps": 1.2, "payload_kg": 20.0, "battery_life_h": 4.0, "has_dexterous_hands": True, "finger_count": 5, "can_climb_stairs": True, "can_navigate_rough_terrain": True, "autonomy_level": "semi", "has_estop": True, "force_limited_joints": True, "has_sdk": True, "has_api": True, "has_support_sla": True, "commercial_deployments": 50, "height_cm": 175, "weight_kg": 75}},
    {"name": "Humanoid HMND 01 Alpha Wheeled", "vendor": "Humanoid (SKL Robotics)", "model_slug": "humanoid-hmnd01-alpha-wheeled", "product_url": "https://thehumanoid.ai/", "vendor_url": "https://thehumanoid.ai", "vendor_aliases": "Humanoid|HMND|SKL Robotics|SKL Robotics LTD|thehumanoid", "robot_aliases": "HMND 01|HMND 01 Alpha Wheeled|Alpha Wheeled", "verification_status": "VERIFIED", "status": "pilot", "country": "UK", "specs": {"top_speed_mps": 1.5, "payload_kg": 25.0, "battery_life_h": 5.0, "has_dexterous_hands": True, "finger_count": 5, "can_navigate_rough_terrain": True, "autonomy_level": "semi", "has_estop": True, "force_limited_joints": True, "has_sdk": True, "has_api": True, "has_support_sla": True, "commercial_deployments": 30, "height_cm": 170, "weight_kg": 80}},
    {"name": "EngineAI PM01", "vendor": "EngineAI", "model_slug": "engineai-pm01", "product_url": "https://en.engineai.com.cn/", "vendor_url": "https://www.engineai.com", "vendor_name_cn": "众擎机器人", "vendor_aliases": "EngineAI|众擎机器人|Zhongqing Robotics", "status": "pilot", "country": "China"},
    {"name": "EngineAI T800", "vendor": "EngineAI", "model_slug": "engineai-t800", "product_url": "https://en.engineai.com.cn/", "vendor_url": "https://www.engineai.com", "vendor_name_cn": "众擎机器人", "vendor_aliases": "EngineAI|众擎机器人|Zhongqing Robotics", "status": "research", "country": "China"},
    {"name": "Fourier GR-1", "vendor": "Fourier Intelligence", "model_slug": "fourier-gr1", "product_url": "https://www.fftai.com/products-gr1", "vendor_url": "https://www.fftai.com", "vendor_name_cn": "傅利叶", "vendor_aliases": "Fourier|傅利叶|傅利叶智能|Fourier Intelligence|Fourier Robotics", "robot_aliases": "GR-1|GR1|Fourier GR-1", "verification_status": "VERIFIED", "status": "pilot", "country": "China"},
    {"name": "Fourier GR-2", "vendor": "Fourier Intelligence", "model_slug": "fourier-gr2", "product_url": "https://www.fftai.com/products-gr2", "vendor_url": "https://www.fftai.com", "vendor_name_cn": "傅利叶", "vendor_aliases": "Fourier|傅利叶|傅利叶智能|Fourier Intelligence|Fourier Robotics", "robot_aliases": "GR-2|GR2|Fourier GR-2", "verification_status": "VERIFIED", "status": "pilot", "country": "China"},
    {"name": "Fourier GR-3", "vendor": "Fourier Intelligence", "model_slug": "fourier-gr3", "product_url": "https://www.fftai.com/products-gr3series", "vendor_url": "https://www.fftai.com", "vendor_name_cn": "傅利叶", "vendor_aliases": "Fourier|傅利叶|傅利叶智能|Fourier Intelligence|Fourier Robotics", "robot_aliases": "GR-3|GR3|Fourier GR-3", "verification_status": "VERIFIED", "status": "pilot", "country": "China", "specs": {"top_speed_mps": 1.67, "payload_kg": 3.0, "battery_life_h": 3.0, "charge_time_h": 1.5, "has_dexterous_hands": True, "finger_count": 12, "can_climb_stairs": False, "can_navigate_rough_terrain": True, "can_run": False, "autonomy_level": "semi", "has_estop": True, "force_limited_joints": True, "collision_force_n": 150, "has_sdk": True, "has_api": True, "has_support_sla": True, "commercial_deployments": 10, "height_cm": 165, "weight_kg": 71, "hot_swap_battery": True}},
    {"name": "Fourier GR-3C Cosmo", "vendor": "Fourier Intelligence", "model_slug": "fourier-gr3c", "product_url": "https://www.fftai.com/products-gr3series", "vendor_url": "https://www.fftai.com", "vendor_name_cn": "傅利叶", "vendor_aliases": "Fourier|傅利叶|傅利叶智能|Fourier Intelligence|Fourier Robotics", "robot_aliases": "GR-3C|GR-3C Cosmo|Cosmo", "verification_status": "VERIFIED", "status": "pilot", "country": "China", "specs": {"payload_kg": 3.0, "battery_life_h": 3.0, "has_dexterous_hands": True, "finger_count": 12, "can_navigate_rough_terrain": True, "autonomy_level": "semi", "has_estop": True, "force_limited_joints": True, "has_sdk": True, "has_api": True, "commercial_deployments": 5, "height_cm": 165, "weight_kg": 71, "hot_swap_battery": True}},
    {"name": "XPeng PX5", "vendor": "XPeng Robotics", "model_slug": "xpeng-px5", "product_url": "https://www.xpeng.com", "vendor_url": "https://www.xpeng.com", "vendor_name_cn": "小鹏", "vendor_aliases": "XPeng|小鹏|小鹏汽车|XPeng Motors", "robot_aliases": "XPeng PX5|PX5", "status": "pilot", "country": "China"},
    {"name": "XPeng Iron", "vendor": "XPeng Robotics", "model_slug": "xpeng-iron", "product_url": "https://www.xpeng.com", "vendor_url": "https://www.xpeng.com", "vendor_name_cn": "小鹏", "robot_name_cn": "小鹏IRON", "vendor_aliases": "XPeng|小鹏|小鹏汽车|XPeng Motors", "robot_aliases": "XPeng Iron|IRON|小鹏IRON", "status": "research", "country": "China"},
    {"name": "Leju Kuavo", "vendor": "Leju Robotics", "model_slug": "leju-kuavo", "product_url": "https://www.lejurobotics.com", "vendor_url": "https://www.lejurobot.com", "vendor_name_cn": "乐聚机器人", "robot_name_cn": "夸父", "vendor_aliases": "Leju|乐聚机器人|Leju Robotics", "robot_aliases": "Kuavo|夸父|Kuafu", "status": "pilot", "country": "China"},
    {
        "name": "Neura 4NE1",
        "vendor": "Neura Robotics",
        "model_slug": "neura-4ne1",
        "product_url": "https://neura-robotics.com/",
        "status": "available",
        "country": "Germany",
        "specs": {
            "top_speed_mps": 1.2,
            "payload_kg": 15.0,
            "battery_life_h": 5.0,
            "has_dexterous_hands": True,
            "finger_count": 5,
            "can_climb_stairs": True,
            "can_navigate_rough_terrain": True,
            "autonomy_level": "semi",
            "has_estop": True,
            "force_limited_joints": True,
            "safety_certified": False,
            "has_sdk": True,
            "has_api": True,
            "has_support_sla": True,
            "commercial_deployments": 25,
            "height_cm": 175,
            "weight_kg": 80,
            "hot_swap_battery": True,
        },
    },
    {
        "name": "Hexagon AEON",
        "vendor": "Hexagon Robotics",
        "model_slug": "hexagon-aeon",
        "product_url": "https://robotics.hexagon.com/",
        "status": "pilot",
        "country": "Switzerland",
        "specs": {
            "top_speed_mps": 1.0,
            "payload_kg": 12.0,
            "battery_life_h": 4.0,
            "has_dexterous_hands": True,
            "finger_count": 5,
            "can_climb_stairs": True,
            "can_navigate_rough_terrain": True,
            "autonomy_level": "semi",
            "has_estop": True,
            "force_limited_joints": True,
            "has_sdk": True,
            "has_api": True,
            "has_support_sla": True,
            "commercial_deployments": 5,
            "height_cm": 170,
            "weight_kg": 75,
        },
    },
    {"name": "PAL Robotics TALOS", "vendor": "PAL Robotics", "model_slug": "pal-talos", "product_url": "https://pal-robotics.com", "status": "research", "country": "Spain"},
    {"name": "PAL Robotics REEM-C", "vendor": "PAL Robotics", "model_slug": "pal-reem-c", "product_url": "https://pal-robotics.com", "status": "research", "country": "Spain"},
    {"name": "Engineered Arts Ameca", "vendor": "Engineered Arts", "model_slug": "engineered-arts-ameca", "product_url": "https://engineeredarts.com", "status": "available", "country": "UK"},
    {"name": "Reflex Humanoid", "vendor": "Reflex Robotics", "model_slug": "reflex-humanoid", "product_url": "https://www.reflexrobotics.com", "vendor_url": "https://www.reflexrobotics.com", "vendor_aliases": "Reflex|Reflex Robotics", "robot_aliases": "Reflex|Reflex Humanoid", "verification_status": "VERIFIED", "status": "pilot", "country": "USA"},
    {"name": "MenteeBot", "vendor": "Mentee Robotics", "model_slug": "mentee-bot", "product_url": "https://www.menteebot.com", "status": "pilot", "country": "Israel"},
    {"name": "Persona AI Gen1", "vendor": "Persona AI", "model_slug": "persona-ai-gen1", "product_url": "https://persona.ai", "status": "pilot", "country": "USA", "specs": {"has_dexterous_hands": True, "finger_count": 5, "payload_kg": 5.0, "autonomy_level": "semi", "commercial_deployments": 5, "has_sdk": False, "has_api": False, "has_estop": True, "force_limited_joints": True}},
    {"name": "Xiaomi CyberOne", "vendor": "Xiaomi", "model_slug": "cyberone", "product_url": "https://www.mi.com/global/discover/article?id=1911", "vendor_url": "https://www.mi.com/global", "vendor_name_cn": "小米科技", "robot_name_cn": "铁大 CyberOne", "vendor_aliases": "Xiaomi|小米|小米科技", "robot_aliases": "CyberOne|铁大|Xiaomi CyberOne|CyberOne Pro|xiaomi-cyberone", "verification_status": "VERIFIED", "status": "research", "country": "China"},
    {"name": "Toyota T-HR3", "vendor": "Toyota", "model_slug": "t-hr3", "product_url": "https://global.toyota/en/newsroom/corporate/19634557.html", "vendor_url": "https://global.toyota/en", "vendor_name_cn": "丰田汽车", "robot_name_cn": "T-HR3", "vendor_aliases": "Toyota|丰田|丰田汽车", "robot_aliases": "T-HR3|THR3|Toyota T-HR3|toyota-thr3", "verification_status": "VERIFIED", "status": "research", "country": "Japan"},
    {"name": "Honda ASIMO Successor", "vendor": "Honda", "model_slug": "honda-asimo-successor", "product_url": "https://global.honda/en/robotics/", "vendor_url": "https://global.honda", "vendor_aliases": "Honda|Honda Robotics|本田", "robot_aliases": "ASIMO|ASIMO Successor", "status": "research", "country": "Japan"},
    {
        "name": "Rainbow HUBO2",
        "vendor": "Rainbow Robotics",
        "model_slug": "rainbow-hubo",
        "product_url": "https://www.rainbow-robotics.com/en_hubo2",
        "status": "available",
        "country": "South Korea",
        "specs": {
            "top_speed_mps": 0.8,
            "payload_kg": 5.0,
            "battery_life_h": 2.5,
            "has_dexterous_hands": True,
            "finger_count": 5,
            "can_climb_stairs": False,
            "can_navigate_rough_terrain": True,
            "autonomy_level": "research",
            "has_estop": True,
            "force_limited_joints": True,
            "has_sdk": True,
            "has_api": True,
            "has_support_sla": True,
            "commercial_deployments": 50,
            "height_cm": 120,
            "weight_kg": 43,
        },
    },
    {"name": "Preferred Networks Humanoid", "vendor": "Preferred Networks", "model_slug": "pfn-humanoid", "product_url": "https://preferred.jp", "status": "research", "country": "Japan"},
    # ── China startups & scale players ───────────────────────────────────────
    {"name": "Dexmate Vega", "vendor": "Dexmate", "model_slug": "dexmate-vega", "product_url": "https://www.dexmate.ai/product/vega", "status": "available", "country": "USA", "specs": {"top_speed_mps": 1.1, "payload_kg": 7.0, "battery_life_h": 10.0, "charge_time_h": 2.0, "has_dexterous_hands": True, "finger_count": 10, "can_climb_stairs": False, "can_navigate_rough_terrain": True, "can_run": False, "autonomy_level": "semi", "has_estop": True, "force_limited_joints": True, "collision_force_n": 150, "price_usd": 89999, "has_sdk": True, "has_api": True, "has_support_sla": True, "commercial_deployments": 10, "height_cm": 171, "weight_kg": 135, "hot_swap_battery": False}},
    {"name": "Eden Robot", "vendor": "Eden Robotics", "model_slug": "eden-robotics", "product_url": "https://edenrobotics.ai", "status": "pilot", "country": "USA", "specs": {"autonomy_level": "semi", "has_sdk": True, "has_api": True, "has_estop": True, "commercial_deployments": 1, "has_support_sla": True}},
    {"name": "Noble Machines", "vendor": "Noble Machines", "model_slug": "noble-machines", "product_url": "https://www.noblemachines.ai", "status": "pilot", "country": "USA", "specs": {"top_speed_mps": 0.8, "payload_kg": 23.0, "battery_life_h": 5.0, "can_climb_stairs": True, "can_navigate_rough_terrain": True, "can_run": False, "has_dexterous_hands": True, "finger_count": 5, "autonomy_level": "semi", "has_estop": True, "force_limited_joints": True, "has_sdk": True, "has_api": True, "commercial_deployments": 5, "has_support_sla": True}},
    {"name": "Astribot S1", "vendor": "Stardust Intelligence", "model_slug": "astribot-s1", "product_url": "https://www.astribot.com/en/product", "vendor_url": "https://www.astribot.com", "vendor_name_cn": "星尘智能", "robot_name_cn": "Astribot S1", "vendor_aliases": "星尘智能|Astribot|Stardust Intelligence", "robot_aliases": "Astribot S1", "verification_status": "VERIFIED", "status": "pilot", "country": "China", "specs": {"has_dexterous_hands": True, "finger_count": 5, "autonomy_level": "semi", "has_sdk": True, "commercial_deployments": 5}},
    {"name": "Astribot T1", "vendor": "Stardust Intelligence", "model_slug": "astribot-t1", "product_url": "https://www.astribot.com/en/product", "vendor_url": "https://www.astribot.com", "vendor_name_cn": "星尘智能", "vendor_aliases": "星尘智能|Astribot|Stardust Intelligence", "robot_aliases": "Astribot T1", "verification_status": "PARTIAL", "status": "research", "country": "China"},
    {"name": "Galbot G1", "vendor": "Galbot", "model_slug": "galbot-g1", "product_url": "https://www.galbot.com", "vendor_url": "https://www.galbot.com", "vendor_name_cn": "银河通用", "vendor_aliases": "Galbot|银河通用|银河通用机器人", "robot_aliases": "Galbot G1|G1", "status": "pilot", "country": "China"},
    {"name": "Robotera STAR1", "vendor": "Robotera", "model_slug": "robotera-star1", "product_url": "https://www.robotera.com", "vendor_url": "https://www.robotera.com", "vendor_name_cn": "星动纪元", "vendor_aliases": "Robotera|RobotEra|星动纪元", "robot_aliases": "Robotera STAR1|STAR1|Star1", "status": "pilot", "country": "China", "specs": {"autonomy_level": "semi", "has_dexterous_hands": True, "has_sdk": True, "commercial_deployments": 5}},
    {"name": "LimX TRON 1", "vendor": "LimX Dynamics", "model_slug": "limx-tron1", "product_url": "https://www.limxdynamics.com/en", "vendor_url": "https://www.limxdynamics.com", "vendor_name_cn": "逐际动力", "vendor_aliases": "LimX|LimX Dynamics|逐际动力", "robot_aliases": "TRON1|TRON 1|LimX TRON1", "status": "pilot", "country": "China", "specs": {"autonomy_level": "research", "has_sdk": True, "has_api": True, "commercial_deployments": 3}},
    {"name": "LimX Luna", "vendor": "LimX Dynamics", "model_slug": "limx-luna", "product_url": "https://www.limxdynamics.com/en", "vendor_url": "https://www.limxdynamics.com", "vendor_name_cn": "逐际动力", "vendor_aliases": "LimX|LimX Dynamics|逐际动力", "robot_aliases": "Luna|LimX Luna", "status": "pilot", "country": "China", "specs": {"has_dexterous_hands": True, "autonomy_level": "semi", "has_sdk": True, "commercial_deployments": 2}},
    {"name": "LimX Oli", "vendor": "LimX Dynamics", "model_slug": "limx-oli", "product_url": "https://www.limxdynamics.com/en", "vendor_url": "https://www.limxdynamics.com", "vendor_name_cn": "逐际动力", "vendor_aliases": "LimX|LimX Dynamics|逐际动力", "robot_aliases": "Oli|LimX Oli", "status": "pilot", "country": "China", "specs": {"has_dexterous_hands": True, "autonomy_level": "semi", "has_sdk": True, "commercial_deployments": 2}},
    {"name": "LimX TRON 2", "vendor": "LimX Dynamics", "model_slug": "limx-tron2", "product_url": "https://www.limxdynamics.com/en", "vendor_url": "https://www.limxdynamics.com", "vendor_name_cn": "逐际动力", "vendor_aliases": "LimX|LimX Dynamics|逐际动力", "robot_aliases": "TRON2|TRON 2|LimX TRON2", "status": "pilot", "country": "China", "specs": {"autonomy_level": "semi", "has_sdk": True, "commercial_deployments": 2}},
    {"name": "Kepler Forerunner K2", "vendor": "Kepler", "model_slug": "kepler-k2", "product_url": "https://www.gotokepler.com/home", "vendor_url": "https://www.gotokepler.com", "vendor_name_cn": "开普勒", "vendor_aliases": "Kepler|开普勒|Kepler Robotics|Kepler Exploration", "robot_aliases": "Forerunner K2|Kepler K2|K2", "verification_status": "VERIFIED", "status": "pilot", "country": "China", "specs": {"autonomy_level": "semi", "has_dexterous_hands": True, "commercial_deployments": 3}},
    {"name": "Booster T1", "vendor": "Booster Robotics", "model_slug": "booster-t1", "product_url": "https://www.booster.tech", "vendor_url": "https://www.booster.tech", "vendor_name_cn": "加速进化", "robot_name_cn": "T1", "vendor_aliases": "Booster|加速进化|Booster Robotics", "robot_aliases": "Booster T1|T1", "status": "pilot", "country": "China", "specs": {"autonomy_level": "semi", "has_dexterous_hands": True, "commercial_deployments": 2}},
    {"name": "Matrix Robotics MATRIX-3", "vendor": "Matrix Robotics", "model_slug": "matrix-3", "product_url": "https://matrixrobotics.ai", "status": "pilot", "country": "China", "specs": {"has_dexterous_hands": True, "finger_count": 27, "autonomy_level": "semi", "has_sdk": True, "commercial_deployments": 1, "force_limited_joints": True, "has_estop": True}},
    {"name": "MagicLab MagicBot Gen1", "vendor": "MagicLab", "model_slug": "magiclab-humanoid", "vendor_url": "https://www.magiclab.top", "vendor_name_cn": "魔法原子", "robot_name_cn": "小麦 Gen1", "vendor_aliases": "Magic Lab|魔法原子|MagicLab Robotics", "robot_aliases": "MagicBot Gen1|小麦 Gen1", "status": "research", "country": "China"},
    {"name": "Spirit AI Xiao Mo", "vendor": "Spirit AI", "model_slug": "spirit-ai-humanoid", "vendor_url": "https://www.spirit-ai.com", "vendor_name_cn": "千寻智能", "robot_name_cn": "小墨", "vendor_aliases": "千寻智能|SpiritAI|Qianxun Intelligence", "robot_aliases": "Xiao Mo|小墨", "status": "research", "country": "China"},
    {"name": "DroidUp Humanoid", "vendor": "DroidUp", "model_slug": "droidup-humanoid", "status": "research", "country": "China"},
    {"name": "Origin Dynamics Humanoid", "vendor": "Origin Dynamics", "model_slug": "origin-dynamics-humanoid", "status": "research", "country": "China"},
    {"name": "PNDbotics Adam", "vendor": "PNDbotics", "model_slug": "pndbotics-adam", "product_url": "https://wiki.pndbotics.com/en/robot/humanoid_robot/", "vendor_url": "https://www.pndbotics.com", "vendor_aliases": "PNDbotics|PND Robotics", "robot_aliases": "Adam|PNDbotics Adam", "verification_status": "VERIFIED", "status": "pilot", "country": "China"},
    {"name": "Noetix N2", "vendor": "Noetix Robotics", "model_slug": "noetix-n2", "product_url": "https://noetixrobotics.com/en", "vendor_url": "https://noetixrobotics.com", "vendor_name_cn": None, "robot_name_cn": "N2", "vendor_aliases": "Noetix|Noetix Robotics|Noetix Robotics (Beijing) Technology", "robot_aliases": "N2|N2 Athlete|Noetix N2", "verification_status": "VERIFIED", "authoritative": ["vendor_name_cn"], "status": "pilot", "country": "China"},
    {"name": "Qinglong (OpenLoong)", "vendor": "Qinglong Bot", "model_slug": "qinglong-humanoid", "vendor_url": "https://www.openloong.org.cn", "vendor_name_cn": "青龙机器人", "robot_name_cn": "青龙", "github_url": "https://github.com/loongOpen", "vendor_aliases": "青龙机器人|Qinglong|QingLoong|OpenLoong|Open Loong|开放原子开源社区", "robot_aliases": "青龙|Qinglong|QingLoong|OpenLoong|开源青龙", "status": "research", "country": "China"},
    {"name": "Tianqing Robotics Humanoid", "vendor": "Tianqing Robotics", "model_slug": "tianqing-humanoid", "status": "research", "country": "China"},
    {"name": "Elephant Robotics Humanoid", "vendor": "Elephant Robotics", "model_slug": "elephant-humanoid", "status": "research", "country": "China"},
    {"name": "CloudMinds Ginger XR", "vendor": "CloudMinds", "model_slug": "cloudminds-ginger-xr", "product_url": "https://www.cloudminds.com", "vendor_url": "https://www.cloudminds.com", "vendor_name_cn": "达闼科技", "vendor_aliases": "CloudMinds|达闼科技|达闼机器人|Cloud Ginger", "robot_aliases": "Ginger XR|Ginger|Cloud Ginger", "status": "pilot", "country": "China"},
    {"name": "Siasun Humanoid", "vendor": "Siasun", "model_slug": "siasun-humanoid", "status": "research", "country": "China"},
    {"name": "Estun Codroid 02", "vendor": "Estun Codroid", "model_slug": "estun-codroid", "product_url": "https://www.codroid.ai/en/", "vendor_url": "https://www.codroid.ai", "vendor_name_cn": "埃斯顿酷卓", "vendor_aliases": "Estun Codroid|Codroid|埃斯顿酷卓|南京埃斯顿酷卓|Estun", "robot_aliases": "Codroid 02|Codroid02|Estun Codroid", "verification_status": "VERIFIED", "status": "pilot", "country": "China"},
    {"name": "Deep Robotics DR01", "vendor": "Deep Robotics", "model_slug": "deep-robotics-dr01", "product_url": "https://www.deeprobotics.cn/en", "vendor_url": "https://www.deeprobotics.cn", "vendor_name_cn": "云深处科技", "vendor_aliases": "Deep Robotics|DEEP Robotics|云深处科技|云深处", "robot_aliases": "DR01|Dr.01|Deep Robotics DR01", "status": "research", "country": "China"},
    {"name": "Deep Robotics DR02", "vendor": "Deep Robotics", "model_slug": "deep-robotics-dr02", "product_url": "https://www.deeprobotics.cn/en/index/dr02.html", "vendor_url": "https://www.deeprobotics.cn", "vendor_name_cn": "云深处科技", "vendor_aliases": "Deep Robotics|DEEP Robotics|云深处科技|云深处", "robot_aliases": "DR02|Dr.02|Deep Robotics DR02", "status": "pilot", "country": "China", "specs": {"can_navigate_rough_terrain": True, "has_dexterous_hands": True, "autonomy_level": "semi", "has_estop": True, "force_limited_joints": True, "has_sdk": True, "has_api": True, "commercial_deployments": 3}},
    {"name": "Lanxin Technology Humanoid", "vendor": "Lanxin Technology", "model_slug": "lanxin-humanoid", "status": "research", "country": "China"},
    {"name": "Matrix Hyper Humanoid", "vendor": "Matrix Hyper", "model_slug": "matrix-hyper-humanoid", "status": "research", "country": "China"},
    {"name": "RealMan RealBOT", "vendor": "RealMan Robotics", "model_slug": "realman-humanoid", "product_url": "https://www.realman-robotics.com/en/products/realbot-humanoid.html", "vendor_url": "https://www.realman-robotics.com", "vendor_name_cn": "睿尔曼智能", "vendor_aliases": "RealMan|RealMan Robotics|Realman|睿尔曼智能", "robot_aliases": "RealBOT|RealMan Humanoid|Realman Humanoid", "verification_status": "VERIFIED", "status": "research", "country": "China"},
    {"name": "JAKA Humanoid", "vendor": "JAKA Robotics", "model_slug": "jaka-humanoid", "status": "research", "country": "China"},
    {"name": "Han's Humanoid", "vendor": "Han's Robot", "model_slug": "hans-humanoid", "status": "research", "country": "China"},
    {"name": "STEP Humanoid", "vendor": "STEP Robotics", "model_slug": "step-humanoid", "status": "research", "country": "China", "verification_status": "NEEDS_VERIFICATION"},
    {"name": "Ti5 Yaoguang Humanoid", "vendor": "Ti5 Robot", "model_slug": "ti5-yaoguang", "product_url": "https://www.ti5robot.com/en/h-col-139.html", "vendor_url": "https://www.ti5robot.com/en", "vendor_name_cn": "钛虎机器人", "robot_name_cn": "曜光人形机器人", "vendor_aliases": "Ti5|Ti5 Robot|钛虎|钛虎机器人|钛虎科技", "robot_aliases": "Yaoguang|曜光|曜光人形机器人|Ti5 Humanoid|ti5-humanoid", "verification_status": "VERIFIED", "status": "research", "country": "China"},
    {"name": "Paxini Humanoid", "vendor": "Paxini Robotics", "model_slug": "paxini-humanoid", "product_url": "https://paxini.com/robot", "vendor_url": "https://paxini.com", "vendor_name_cn": "帕西尼", "vendor_aliases": "Paxini|帕西尼|帕西尼感知科技|PaXini", "robot_aliases": "Paxini Humanoid", "status": "research", "country": "China"},
    {"name": "Rhino Robotics Humanoid", "vendor": "Rhino Robotics", "model_slug": "rhino-humanoid", "status": "research", "country": "China"},
    {"name": "Giant.AI Humanoid", "vendor": "Giant.AI", "model_slug": "giant-ai-humanoid", "status": "research", "country": "China"},
    {"name": "Chery Mornine", "vendor": "Chery Robotics", "model_slug": "chery-mornine", "product_url": "https://www.cheryinternational.com", "vendor_url": "https://www.cheryinternational.com", "vendor_name_cn": "奇瑞", "vendor_aliases": "Chery|奇瑞|Chery Robotics|奇瑞汽车", "robot_aliases": "Mornine|Chery Mornine", "status": "pilot", "country": "China"},
    {"name": "Haier Humanoid", "vendor": "Haier Robotics", "model_slug": "haier-humanoid", "status": "research", "country": "China"},
    {"name": "Geely Humanoid", "vendor": "Geely Robotics", "model_slug": "geely-humanoid", "status": "research", "country": "China"},
    {"name": "BYD Humanoid", "vendor": "BYD Robotics", "model_slug": "byd-humanoid", "status": "research", "country": "China"},
    {"name": "NIO Humanoid", "vendor": "NIO Robotics", "model_slug": "nio-humanoid", "status": "research", "country": "China"},
    {"name": "Li Auto Humanoid", "vendor": "Li Auto Robotics", "model_slug": "liauto-humanoid", "status": "research", "country": "China"},
    {"name": "ZTE Humanoid", "vendor": "ZTE Robotics", "model_slug": "zte-humanoid", "status": "research", "country": "China"},
    {"name": "Huawei Humanoid", "vendor": "Huawei Robotics", "model_slug": "huawei-humanoid", "status": "research", "country": "China"},
    {"name": "SenseTime Humanoid", "vendor": "SenseTime", "model_slug": "sensetime-humanoid", "status": "research", "country": "China"},
    {"name": "Megvii Humanoid", "vendor": "Megvii", "model_slug": "megvii-humanoid", "status": "research", "country": "China"},
    {"name": "Horizon Humanoid", "vendor": "Horizon Robotics", "model_slug": "horizon-humanoid", "status": "research", "country": "China"},
    {"name": "DJI Humanoid", "vendor": "DJI Robotics", "model_slug": "dji-humanoid", "status": "research", "country": "China"},
    {"name": "Dreame Humanoid", "vendor": "Dreame Robotics", "model_slug": "dreame-humanoid", "status": "research", "country": "China"},
    {"name": "Ecovacs Humanoid", "vendor": "Ecovacs Robotics", "model_slug": "ecovacs-humanoid", "status": "research", "country": "China"},
    {"name": "Roborock Humanoid", "vendor": "Roborock", "model_slug": "roborock-humanoid", "status": "research", "country": "China"},
    {"name": "Ninebot Humanoid", "vendor": "Ninebot Robotics", "model_slug": "ninebot-humanoid", "status": "research", "country": "China"},
    {"name": "Segway Humanoid", "vendor": "Segway Robotics", "model_slug": "segway-humanoid", "product_url": "https://www.segwayrobotics.com", "vendor_url": "https://www.segwayrobotics.com", "vendor_name_cn": "九号公司", "vendor_aliases": "Segway|Segway Robotics|Ninebot|九号公司|赛格威", "robot_aliases": "Segway Humanoid", "verification_status": "NEEDS_VERIFICATION", "status": "research", "country": "China"},
    {"name": "CloudWalk Humanoid", "vendor": "CloudWalk", "model_slug": "cloudwalk-humanoid", "status": "research", "country": "China"},
    {"name": "Iflytek Humanoid", "vendor": "Iflytek Robotics", "model_slug": "iflytek-humanoid", "status": "research", "country": "China"},
    {"name": "Baidu Humanoid", "vendor": "Baidu Robotics", "model_slug": "baidu-humanoid", "status": "research", "country": "China"},
    {"name": "Alibaba Humanoid", "vendor": "Alibaba DAMO Academy", "model_slug": "alibaba-humanoid", "status": "research", "country": "China"},
    {"name": "Tencent Humanoid", "vendor": "Tencent Robotics", "model_slug": "tencent-humanoid", "status": "research", "country": "China"},
    {"name": "ByteDance Humanoid", "vendor": "ByteDance Robotics", "model_slug": "bytedance-humanoid", "status": "research", "country": "China"},
    {"name": "Meituan Humanoid", "vendor": "Meituan Robotics", "model_slug": "meituan-humanoid", "status": "research", "country": "China"},
    {"name": "JD Humanoid", "vendor": "JD Robotics", "model_slug": "jd-humanoid", "status": "research", "country": "China"},
    {"name": "SF Express Humanoid", "vendor": "SF Express Robotics", "model_slug": "sf-humanoid", "status": "research", "country": "China"},
    {"name": "Cainiao Humanoid", "vendor": "Cainiao Robotics", "model_slug": "cainiao-humanoid", "status": "research", "country": "China"},
    {"name": "Geek+ Humanoid", "vendor": "Geek+", "model_slug": "geekplus-humanoid", "status": "research", "country": "China"},
    {"name": "Hai Robotics Humanoid", "vendor": "Hai Robotics", "model_slug": "hai-humanoid", "status": "research", "country": "China"},
    {"name": "Quicktron Humanoid", "vendor": "Quicktron Robotics", "model_slug": "quicktron-humanoid", "status": "research", "country": "China"},
    {"name": "ForwardX Humanoid", "vendor": "ForwardX Robotics", "model_slug": "forwardx-humanoid", "status": "research", "country": "China"},
    {"name": "VisionNav Humanoid", "vendor": "VisionNav Robotics", "model_slug": "visionnav-humanoid", "status": "research", "country": "China"},
    {"name": "Syrius Humanoid", "vendor": "Syrius Robotics", "model_slug": "syrius-humanoid", "product_url": "https://www.syriusrobotics.com", "vendor_url": "https://www.syriusrobotics.com", "vendor_name_cn": "仙工智能", "robot_name_cn": "人形机器人", "vendor_aliases": "Syrius|Syrius Robotics|仙工智能", "robot_aliases": "Syrius Humanoid|人形机器人", "verification_status": "PARTIAL", "status": "research", "country": "China"},
    {"name": "Youibot Humanoid", "vendor": "Youibot", "model_slug": "youibot-humanoid", "status": "research", "country": "China"},
    {"name": "Standard Robots Humanoid", "vendor": "Standard Robots", "model_slug": "standard-robots-humanoid", "status": "research", "country": "China"},
    {"name": "Seer Humanoid", "vendor": "SEER Robotics", "model_slug": "seer-humanoid", "product_url": "https://www.seer-robotics.ai", "vendor_url": "https://www.seer-robotics.ai", "vendor_aliases": "SEER|SEER Robotics", "robot_aliases": "Seer Humanoid", "verification_status": "PARTIAL", "status": "research", "country": "China"},
    {"name": "HIT Robot Group Humanoid", "vendor": "HIT Robot Group", "model_slug": "hit-humanoid", "status": "research", "country": "China"},
    {"name": "Pangolin Humanoid", "vendor": "Pangolin Robot", "model_slug": "pangolin-humanoid", "product_url": "https://www.pangolin-robot.com", "vendor_url": "https://www.pangolin-robot.com", "vendor_name_cn": "穿山甲机器人", "robot_name_cn": "人形机器人", "vendor_aliases": "Pangolin|Pangolin Robot|穿山甲机器人|Suzhou Pangolin", "robot_aliases": "Pangolin Humanoid|Suzhou Pangolin Humanoid|人形机器人", "verification_status": "PARTIAL", "status": "research", "country": "China"},
    {"name": "Elephant Paxini Humanoid", "vendor": "Elephant Paxini", "model_slug": "elephant-paxini-humanoid", "status": "research", "country": "China"},
    {"name": "Clone Alpha", "vendor": "Clone Robotics", "model_slug": "clone-alpha", "product_url": "https://clonerobotics.com/", "vendor_url": "https://clonerobotics.com", "vendor_aliases": "Clone|Clone Robotics", "robot_aliases": "Clone Alpha|Clone|Neoclone", "verification_status": "VERIFIED", "status": "research", "country": "Poland"},
    {"name": "Halodi Eve", "vendor": "Halodi Robotics", "model_slug": "halodi-eve", "status": "research", "country": "Norway"},
    {"name": "Shadow Dexterous Hand Platform", "vendor": "Shadow Robot Company", "model_slug": "shadow-hand-platform", "product_url": "https://www.shadowrobot.com/dexterous-hand-series/", "vendor_url": "https://www.shadowrobot.com", "vendor_aliases": "Shadow|Shadow Robot|Shadow Robot Company", "robot_aliases": "Shadow Hand|Shadow Dexterous Hand|Dexterous Hand Platform", "verification_status": "VERIFIED", "status": "research", "country": "UK"},
    {"name": "IHMC Atlas Research", "vendor": "IHMC Robotics", "model_slug": "ihmc-atlas", "status": "research", "country": "USA"},
    {"name": "NASA Valkyrie", "vendor": "NASA Johnson", "model_slug": "nasa-valkyrie", "product_url": "https://www.nasa.gov/technology/r5/", "vendor_url": "https://www.nasa.gov", "humanoid_guide_url": "https://www.nasa.gov/wp-content/uploads/2023/06/r5-fact-sheet.pdf", "vendor_aliases": "NASA|NASA Johnson|NASA JSC", "robot_aliases": "Valkyrie|R5|NASA R5|NASA Valkyrie", "verification_status": "VERIFIED", "status": "research", "country": "USA"},
    {"name": "DLR TORO", "vendor": "DLR", "model_slug": "dlr-toro", "product_url": "https://www.dlr.de/en/rm/research/robotic-systems/humanoids/toro", "vendor_url": "https://www.dlr.de", "humanoid_guide_url": "https://ieeexplore.ieee.org/document/7041461", "vendor_aliases": "DLR|German Aerospace Center|Deutsches Zentrum für Luft- und Raumfahrt", "robot_aliases": "TORO|Torque-controlled humanoid Robot", "verification_status": "VERIFIED", "status": "research", "country": "Germany", "specs": {"height_cm": 174, "weight_kg": 76, "payload_kg": 10.0, "top_speed_mps": 0.5, "force_limited_joints": True, "autonomy_level": "research", "commercial_deployments": 0}},
    {"name": "DLR Rollin' Justin", "vendor": "DLR", "model_slug": "dlr-justin", "status": "research", "country": "Germany"},
    {"name": "Kawasaki Kaleido", "vendor": "Kawasaki Heavy Industries", "model_slug": "kawasaki-kaleido", "product_url": "https://kawasakirobotics.com/asia-oceania/blog/category/kaleido-humanoid-robot/", "vendor_url": "https://kawasakirobotics.com", "vendor_name_cn": "川崎重工", "vendor_aliases": "Kawasaki|Kawasaki Robotics|Kawasaki Heavy Industries|川崎重工", "robot_aliases": "Kaleido|RHP|Robust Humanoid Platform|RHP7|Kaleido9", "verification_status": "VERIFIED", "status": "research", "country": "Japan"},
    {"name": "Honda Avatar", "vendor": "Honda", "model_slug": "honda-avatar", "product_url": "https://global.honda/en/robotics/", "vendor_url": "https://global.honda", "vendor_aliases": "Honda|Honda Robotics|本田|Honda R&D", "robot_aliases": "Honda Avatar|Avatar Robot", "verification_status": "VERIFIED", "status": "research", "country": "Japan"},
    {"name": "Pepper", "vendor": "SoftBank Robotics", "model_slug": "pepper", "product_url": "https://www.softbankrobotics.com/emea/en/pepper", "vendor_url": "https://www.softbankrobotics.com", "vendor_name_cn": "软银机器人", "robot_name_cn": "Pepper", "vendor_aliases": "SoftBank|SoftBank Robotics|软银机器人", "robot_aliases": "Pepper|Pepper Next|softbank-pepper-next", "verification_status": "VERIFIED", "status": "research", "country": "Japan"},
    {"name": "Toyota Punyo", "vendor": "Toyota Research Institute", "model_slug": "punyo", "product_url": "https://punyo.tech", "vendor_url": "https://www.tri.global", "vendor_name_cn": "丰田研究院", "robot_name_cn": "Punyo", "vendor_aliases": "TRI|Toyota Research Institute|丰田研究院", "robot_aliases": "Punyo|Toyota Punyo|toyota-punyo", "verification_status": "VERIFIED", "status": "research", "country": "Japan"},
    {"name": "Samsung Bot Handy", "vendor": "Samsung Research", "model_slug": "samsung-bot-handy", "product_url": "https://research.samsung.com/news/-CES-2022-Samsung-Research-New-Tech-Trio-Samsung-Bot-Handy-Housework-robot", "vendor_url": "https://research.samsung.com", "vendor_aliases": "Samsung|Samsung Research|Samsung Electronics", "robot_aliases": "Bot Handy|Samsung Bot Handy", "verification_status": "VERIFIED", "status": "research", "country": "South Korea"},
    {"name": "LG CLOi SuitBot", "vendor": "LG Electronics", "model_slug": "lg-cloi-suitbot", "product_url": "https://www.lg.com/uk/lg-experience/lg-lab/ifa-2018-your-ultimate-guide-to-lg-cloi-robots/", "vendor_url": "https://www.lg.com", "vendor_aliases": "LG|LG Electronics|LG CLOi", "robot_aliases": "CLOi SuitBot|CLOi|LG CLOi SuitBot", "verification_status": "VERIFIED", "status": "research", "country": "South Korea"},
    {"name": "Hyundai Boston Dynamics Atlas", "vendor": "Hyundai Robotics", "model_slug": "hyundai-atlas", "status": "pilot", "country": "South Korea"},
    {"name": "Skydio Humanoid Research", "vendor": "Skydio Robotics Lab", "model_slug": "skydio-humanoid", "status": "research", "country": "USA"},
    {"name": "Amazon Digit Pilot", "vendor": "Amazon Robotics", "model_slug": "amazon-digit", "status": "pilot", "country": "USA"},
    {"name": "BMW Figure Pilot", "vendor": "BMW Manufacturing", "model_slug": "bmw-figure-pilot", "status": "pilot", "country": "Germany"},
    {"name": "Mercedes Apptronik Pilot", "vendor": "Mercedes-Benz", "model_slug": "mercedes-apptronik", "status": "pilot", "country": "Germany"},
    {"name": "BMW Apptronik Pilot", "vendor": "BMW Group", "model_slug": "bmw-apptronik", "status": "pilot", "country": "Germany"},
    {"name": "GXO Agility Digit", "vendor": "GXO Logistics", "model_slug": "gxo-digit", "status": "pilot", "country": "USA"},
    {"name": "Schaeffler Neura 4NE1", "vendor": "Schaeffler", "model_slug": "schaeffler-4ne1", "status": "pilot", "country": "Germany"},
    {"name": "Mercedes Figure Pilot", "vendor": "Mercedes-Benz Manufacturing", "model_slug": "mercedes-figure", "status": "pilot", "country": "Germany"},
    {"name": "BMW Figure Pilot", "vendor": "BMW Manufacturing", "model_slug": "bmw-figure", "status": "pilot", "country": "Germany"},
    {"name": "Foxconn Optimus Pilot", "vendor": "Foxconn", "model_slug": "foxconn-optimus", "status": "pilot", "country": "Taiwan"},
    {"name": "Foxconn Unitree Pilot", "vendor": "Foxconn", "model_slug": "foxconn-unitree", "status": "pilot", "country": "Taiwan"},
    {"name": "NVIDIA GR00T Partner Humanoid", "vendor": "NVIDIA Robotics", "model_slug": "nvidia-gr00t-humanoid", "status": "research", "country": "USA"},
    {"name": "Physical Intelligence Research", "vendor": "Physical Intelligence", "model_slug": "pi-humanoid-research", "status": "research", "country": "USA"},
    {"name": "Skild AI Foundation Model", "vendor": "Skild AI", "model_slug": "skild-humanoid-stack", "status": "research", "country": "USA"},
    {"name": "Covariant Humanoid Stack", "vendor": "Covariant", "model_slug": "covariant-humanoid", "status": "research", "country": "USA"},
    {"name": "OpenAI Humanoid Partner", "vendor": "OpenAI Robotics", "model_slug": "openai-humanoid-partner", "status": "research", "country": "USA"},
    {"name": "Meta FAIR Humanoid", "vendor": "Meta FAIR", "model_slug": "meta-fair-humanoid", "status": "research", "country": "USA"},
    {"name": "Google DeepMind Humanoid", "vendor": "Google DeepMind", "model_slug": "deepmind-humanoid", "status": "research", "country": "UK"},
    {"name": "Waymo Humanoid Research", "vendor": "Waymo", "model_slug": "waymo-humanoid", "status": "research", "country": "USA"},
    {"name": "Apple Robotics Humanoid", "vendor": "Apple Robotics", "model_slug": "apple-humanoid", "status": "research", "country": "USA"},
    {"name": "Microsoft Azure Humanoid", "vendor": "Microsoft Robotics", "model_slug": "microsoft-humanoid", "status": "research", "country": "USA"},
    {"name": "Intel Humanoid Lab", "vendor": "Intel Labs", "model_slug": "intel-humanoid", "status": "research", "country": "USA"},
    {"name": "Qualcomm Humanoid Platform", "vendor": "Qualcomm", "model_slug": "qualcomm-humanoid", "status": "research", "country": "USA"},
    {"name": "AMD Humanoid Platform", "vendor": "AMD", "model_slug": "amd-humanoid", "status": "research", "country": "USA"},
    {"name": "ARM Humanoid Platform", "vendor": "ARM Robotics", "model_slug": "arm-humanoid", "status": "research", "country": "UK"},
    {"name": "Siemens Humanoid Pilot", "vendor": "Siemens", "model_slug": "siemens-humanoid", "status": "research", "country": "Germany"},
    {"name": "ABB Humanoid Research", "vendor": "ABB Robotics", "model_slug": "abb-humanoid", "status": "research", "country": "Switzerland"},
    {"name": "Fanuc Humanoid Research", "vendor": "Fanuc", "model_slug": "fanuc-humanoid", "status": "research", "country": "Japan"},
    {"name": "KUKA Humanoid Research", "vendor": "KUKA", "model_slug": "kuka-humanoid", "status": "research", "country": "Germany"},
    {"name": "Yaskawa Humanoid Research", "vendor": "Yaskawa", "model_slug": "yaskawa-humanoid", "status": "research", "country": "Japan"},
    {"name": "Universal Robots Humanoid", "vendor": "Universal Robots", "model_slug": "ur-humanoid", "status": "research", "country": "Denmark"},
    {"name": "Techman Humanoid", "vendor": "Techman Robot", "model_slug": "techman-humanoid", "status": "research", "country": "Taiwan"},
    {"name": "Doosan Humanoid", "vendor": "Doosan Robotics", "model_slug": "doosan-humanoid", "status": "research", "country": "South Korea"},
    {"name": "Franka Humanoid", "vendor": "Franka Emika", "model_slug": "franka-humanoid", "status": "research", "country": "Germany"},
    {"name": "Comau Humanoid", "vendor": "Comau", "model_slug": "comau-humanoid", "status": "research", "country": "Italy"},
    {"name": "Epson Humanoid", "vendor": "Epson Robotics", "model_slug": "epson-humanoid", "status": "research", "country": "Japan"},
    {"name": "Omron Humanoid", "vendor": "Omron Robotics", "model_slug": "omron-humanoid", "status": "research", "country": "Japan"},
    {"name": "Mitsubishi Humanoid", "vendor": "Mitsubishi Electric", "model_slug": "mitsubishi-humanoid", "status": "research", "country": "Japan"},
    {"name": "Denso Humanoid", "vendor": "Denso Robotics", "model_slug": "denso-humanoid", "status": "research", "country": "Japan"},
    {"name": "Nidec Humanoid", "vendor": "Nidec Robotics", "model_slug": "nidec-humanoid", "status": "research", "country": "Japan"},
    {"name": "Harmonic Drive Humanoid", "vendor": "Harmonic Drive", "model_slug": "harmonic-humanoid", "status": "research", "country": "Japan"},
    {"name": "Maxon Humanoid Actuator Kit", "vendor": "Maxon Group", "model_slug": "maxon-humanoid-kit", "status": "research", "country": "Switzerland"},
    {
        "name": "Tesla Optimus Gen 1",
        "vendor": "Tesla",
        "model_slug": "tesla-optimus-gen1",
        "product_url": "https://www.tesla.com/AI",
        "status": "research",
        "country": "USA",
        "specs": {
            "top_speed_mps": 0.5,
            "payload_kg": 10.0,
            "battery_life_h": 4.0,
            "has_dexterous_hands": True,
            "finger_count": 4,
            "autonomy_level": "teleop",
            "has_estop": True,
            "height_cm": 172,
            "weight_kg": 57,
        },
    },
    {"name": "Sanctuary M-Series", "vendor": "Sanctuary AI", "model_slug": "sanctuary-m-series", "product_url": "https://sanctuary.ai", "vendor_url": "https://sanctuary.ai", "vendor_aliases": "Sanctuary|Sanctuary AI", "robot_aliases": "M-Series|Sanctuary M-Series", "verification_status": "PARTIAL", "status": "research", "country": "Canada"},
    {
        "name": "Agility Digit 2",
        "vendor": "Agility Robotics",
        "model_slug": "agility-digit-2",
        "product_url": "https://www.agilityrobotics.com/solutions",
        "status": "pilot",
        "country": "USA",
        "specs": {
            "top_speed_mps": 1.6,
            "payload_kg": 18.0,
            "battery_life_h": 4.5,
            "can_climb_stairs": True,
            "has_estop": True,
            "safety_certified": True,
            "commercial_deployments": 25,
            "has_sdk": True,
            "has_api": True,
            "has_support_sla": True,
            "hot_swap_battery": True,
        },
    },
    {
        "name": "Figure 03",
        "vendor": "Figure AI",
        "model_slug": "figure-03",
        "product_url": "https://www.figure.ai",
        "status": "research",
        "country": "USA",
        "specs": {
            "top_speed_mps": 1.4,
            "payload_kg": 22.0,
            "battery_life_h": 5.5,
            "has_dexterous_hands": True,
            "finger_count": 5,
            "can_climb_stairs": True,
            "autonomy_level": "semi",
            "has_estop": True,
            "has_support_sla": True,
            "commercial_deployments": 2,
        },
    },
    {"name": "1X NEO Beta", "vendor": "1X Technologies", "model_slug": "1x-neo-beta", "status": "pilot", "country": "USA"},
    {"name": "Zhiyuan Lingxi", "vendor": "Zhiyuan Robotics", "model_slug": "zhiyuan-lingxi", "status": "pilot", "country": "China"},
    {"name": "Leju Kuavo 3", "vendor": "Leju Robotics", "model_slug": "leju-kuavo-3", "product_url": "https://www.lejurobot.com", "vendor_url": "https://www.lejurobot.com", "vendor_name_cn": "乐聚机器人", "robot_name_cn": "夸父3", "vendor_aliases": "Leju|乐聚机器人|Leju Robotics", "robot_aliases": "Kuavo 3|夸父3|Kuafu 3", "status": "pilot", "country": "China"},
    {"name": "Astribot S2", "vendor": "Stardust Intelligence", "model_slug": "astribot-s2", "product_url": "https://www.astribot.com/en/product", "vendor_url": "https://www.astribot.com", "vendor_name_cn": "星尘智能", "status": "research", "country": "China"},
    {"name": "Galbot G2", "vendor": "Galbot", "model_slug": "galbot-g2", "product_url": "https://www.galbot.com", "vendor_url": "https://www.galbot.com", "vendor_name_cn": "银河通用", "vendor_aliases": "Galbot|银河通用|银河通用机器人", "robot_aliases": "Galbot G2|G2", "status": "pilot", "country": "China"},
    {"name": "Robotera STAR2", "vendor": "Robotera", "model_slug": "robotera-star2", "product_url": "https://www.robotera.com", "vendor_url": "https://www.robotera.com", "vendor_name_cn": "星动纪元", "vendor_aliases": "Robotera|RobotEra|星动纪元", "robot_aliases": "Robotera STAR2|STAR2|Star2", "status": "pilot", "country": "China", "specs": {"autonomy_level": "semi", "has_dexterous_hands": True, "has_sdk": True, "commercial_deployments": 3}},
    {"name": "Kepler Forerunner K1", "vendor": "Kepler", "model_slug": "kepler-k1", "product_url": "https://www.gotokepler.com/home", "vendor_url": "https://www.gotokepler.com", "vendor_name_cn": "开普勒", "vendor_aliases": "Kepler|开普勒|Kepler Robotics|Kepler Exploration", "robot_aliases": "Forerunner K1|Kepler K1|K1", "status": "research", "country": "China"},
    {"name": "Booster K1", "vendor": "Booster Robotics", "model_slug": "booster-k1", "product_url": "https://www.booster.tech", "vendor_url": "https://www.booster.tech", "vendor_name_cn": "加速进化", "robot_name_cn": "K1", "vendor_aliases": "Booster|加速进化|Booster Robotics", "robot_aliases": "Booster K1|K1", "status": "research", "country": "China"},
    {"name": "PNDbotics Adam U", "vendor": "PNDbotics", "model_slug": "pndbotics-adam-u", "product_url": "https://wiki.pndbotics.com/en/robot/humanoid_robot/", "vendor_url": "https://www.pndbotics.com", "vendor_aliases": "PNDbotics|PND Robotics", "robot_aliases": "Adam U|PNDbotics Adam U", "verification_status": "VERIFIED", "status": "pilot", "country": "China"},
    {"name": "Noetix E1", "vendor": "Noetix Robotics", "model_slug": "noetix-e1", "product_url": "https://noetixrobotics.com/en/e1", "vendor_url": "https://noetixrobotics.com", "robot_name_cn": "E1", "vendor_aliases": "Noetix|Noetix Robotics|Noetix Robotics (Beijing) Technology", "robot_aliases": "E1|E1 Geek Vanguard|Noetix E1", "verification_status": "VERIFIED", "status": "research", "country": "China", "specs": {"height_cm": 136, "weight_kg": 40, "payload_kg": 5.0, "has_dexterous_hands": True, "finger_count": 5, "peak_torque_nm": 150.0, "peak_torque_note": "Maximum knee torque 150 N\u00b7m (noetixrobotics.com/en/e1)", "battery_life_h": 2.5, "autonomy_level": "semi", "has_sdk": True, "has_api": True}},
    {"name": "EngineAI SA01", "vendor": "EngineAI", "model_slug": "engineai-sa01", "product_url": "https://en.engineai.com.cn/", "vendor_url": "https://en.engineai.com.cn", "vendor_name_cn": "众擎机器人", "vendor_aliases": "EngineAI|众擎机器人|Zhongqing Robotics", "robot_aliases": "SA01|EngineAI SA01", "status": "research", "country": "China"},
    {"name": "Fourier N1", "vendor": "Fourier Intelligence", "model_slug": "fourier-n1", "product_url": "https://www.fftai.com", "vendor_url": "https://www.fftai.com", "vendor_name_cn": "傅利叶", "vendor_aliases": "Fourier|傅利叶|傅利叶智能|Fourier Intelligence|Fourier Robotics", "robot_aliases": "N1|Fourier N1", "status": "research", "country": "China"},
    {"name": "Neura MAiRA", "vendor": "Neura Robotics", "model_slug": "neura-maira", "product_url": "https://neura-robotics.com/products/maira/", "status": "pilot", "country": "Germany"},
    {"name": "PAL Robotics ARI", "vendor": "PAL Robotics", "model_slug": "pal-ari", "product_url": "https://pal-robotics.com/robot/ari/", "vendor_url": "https://pal-robotics.com", "vendor_aliases": "PAL|PAL Robotics", "robot_aliases": "ARI|PAL ARI|PAL Robotics ARI", "verification_status": "VERIFIED", "status": "research", "country": "Spain", "specs": {"height_cm": 165, "battery_life_h": 10.0, "has_api": True, "has_sdk": True, "autonomy_level": "semi"}},
    {"name": "Engineered Arts Mesmer", "vendor": "Engineered Arts", "model_slug": "engineered-arts-mesmer", "status": "available", "country": "UK"},
    {"name": "Reflex Gen2", "vendor": "Reflex Robotics", "model_slug": "reflex-gen2", "product_url": "https://www.reflexrobotics.com", "vendor_url": "https://www.reflexrobotics.com", "vendor_aliases": "Reflex|Reflex Robotics", "robot_aliases": "Reflex Gen2|Gen2", "verification_status": "VERIFIED", "status": "pilot", "country": "USA"},
    {"name": "MenteeBot Pro", "vendor": "Mentee Robotics", "model_slug": "mentee-bot-pro", "status": "pilot", "country": "Israel"},
    {"name": "Persona AI Gen2", "vendor": "Persona AI", "model_slug": "persona-ai-gen2", "product_url": "https://persona.ai", "status": "pilot", "country": "USA"},
]


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:80] or "humanoid"


# Entity-resolution fields synced into humanoid_benchmarks (besides name/status/product_url).
ENTITY_FIELDS = (
    "country",
    "vendor_name_cn",
    "robot_name_cn",
    "vendor_url",
    "humanoid_guide_url",
    "github_url",
    "verification_status",
    # Pipe-delimited alternate spellings (English + native) for crawler recall.
    "vendor_aliases",
    "robot_aliases",
)


def normalize_catalog_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure model_slug and default fields exist."""
    out = dict(entry)
    if not out.get("model_slug"):
        out["model_slug"] = slugify(f"{out.get('vendor', '')}-{out.get('name', '')}")
    out.setdefault("status", "research")
    out.setdefault("specs", {})
    out.setdefault("product_url", None)
    for field in ENTITY_FIELDS:
        out.setdefault(field, None)
    return out


def _authoritative_fields(entry: Dict[str, Any]) -> frozenset:
    """Entity fields the catalog owns outright — written verbatim, including None.

    Set ``"authoritative": True`` on an entry to make the catalog win for every
    entity field (use to scrub stale/wrong data), or pass a list of specific
    field names. Default is fill-only (COALESCE) so enrichment data is preserved.
    """
    auth = entry.get("authoritative")
    if auth is True:
        return frozenset(ENTITY_FIELDS)
    if isinstance(auth, (list, tuple, set)):
        return frozenset(f for f in auth if f in ENTITY_FIELDS)
    return frozenset()


def catalog_entries() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for entry in HUMANOID_CATALOG:
        normalized = normalize_catalog_entry(entry)
        slug = normalized["model_slug"]
        if is_excluded_humanoid_slug(slug):
            continue
        if is_junk_humanoid_row(normalized["name"], normalized["vendor"], slug):
            continue
        out.append(normalized)
    return out


def catalog_count() -> int:
    return len(catalog_entries())


def sync_product_urls_from_catalog(db_session: Any) -> dict:
    """Push curated catalog identity + entity-resolution fields into humanoid_benchmarks.

    Writes name/status/product_url plus the entity-resolution columns (country,
    Chinese names, vendor/guide/github URLs, verification_status). Unlike the old
    behavior, rows without a product_url are still synced so NEEDS_VERIFICATION /
    PARTIAL entities keep their native names and candidate URLs.
    """
    from sqlalchemy import text

    updated = 0
    skipped = 0
    for entry in catalog_entries():
        slug = entry.get("model_slug")
        if not slug:
            skipped += 1
            continue
        params = {
            "slug": slug,
            "name": entry.get("name"),
            "vendor": entry.get("vendor"),
            "status": entry.get("status"),
            "url": entry.get("product_url"),
            **{f: entry.get(f) for f in ENTITY_FIELDS},
        }
        # Build SET / WHERE from ENTITY_FIELDS so new entity fields auto-sync.
        # Authoritative fields are written verbatim (catalog wins, including NULL)
        # so the catalog can scrub stale/wrong data; others are fill-only (COALESCE).
        auth = _authoritative_fields(entry)
        entity_set = ",\n                    ".join(
            (f"{f} = :{f}" if f in auth else f"{f} = COALESCE(:{f}, {f})")
            for f in ENTITY_FIELDS
        )
        entity_diff = "".join(
            (f"\n                    OR {f} IS DISTINCT FROM :{f}" if f in auth
             else f"\n                    OR (:{f} IS NOT NULL AND {f} IS DISTINCT FROM :{f})")
            for f in ENTITY_FIELDS
        )
        result = db_session.execute(
            text(f"""
                UPDATE humanoid_benchmarks
                SET
                    name = :name,
                    vendor = COALESCE(:vendor, vendor),
                    status = :status,
                    product_url = COALESCE(:url, product_url),
                    {entity_set},
                    updated_at = NOW()
                WHERE model_slug = :slug
                  AND (
                    name IS DISTINCT FROM :name
                    OR (:vendor IS NOT NULL AND vendor IS DISTINCT FROM :vendor)
                    OR status IS DISTINCT FROM :status
                    OR (:url IS NOT NULL AND product_url IS DISTINCT FROM :url){entity_diff}
                  )
            """),
            params,
        )
        if result.rowcount:
            updated += 1
        else:
            skipped += 1
    db_session.commit()
    return {
        "updated": updated,
        "skipped": skipped,
        "catalog_urls": sum(1 for e in catalog_entries() if e.get("product_url")),
        "verification_tagged": sum(1 for e in catalog_entries() if e.get("verification_status")),
    }
