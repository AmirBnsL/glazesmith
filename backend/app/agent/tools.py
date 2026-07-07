TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "predict_properties",
            "description": "Predict fired properties (color, surface, crazing risk, CTE) from oxide composition and firing conditions",
            "parameters": {
                "type": "object",
                "properties": {
                    "sio2": {"type": "number"},
                    "al2o3": {"type": "number"},
                    "k2o": {"type": "number"},
                    "na2o": {"type": "number"},
                    "cao": {"type": "number"},
                    "mgo": {"type": "number"},
                    "fe2o3": {"type": "number"},
                    "tio2": {"type": "number"},
                    "b2o3": {"type": "number"},
                    "zno": {"type": "number"},
                    "li2o": {"type": "number"},
                    "cone": {"type": "integer"},
                    "atmosphere": {"type": "string", "enum": ["oxidation", "reduction"]},
                },
                "required": ["sio2", "al2o3", "cao", "cone"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fix_defect",
            "description": "Suggest formulation adjustments to fix a specific glaze defect",
            "parameters": {
                "type": "object",
                "properties": {
                    "defect": {
                        "type": "string",
                        "enum": ["crazing", "crawling", "pinholing", "blistering", "shivering"],
                    },
                    "current_composition": {"type": "object"},
                    "cone": {"type": "integer"},
                },
                "required": ["defect", "current_composition"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_cte",
            "description": "Calculate coefficient of thermal expansion from oxide composition",
            "parameters": {
                "type": "object",
                "properties": {
                    "sio2": {"type": "number"},
                    "al2o3": {"type": "number"},
                    "k2o": {"type": "number"},
                    "na2o": {"type": "number"},
                    "cao": {"type": "number"},
                    "mgo": {"type": "number"},
                },
                "required": ["sio2", "al2o3", "na2o", "k2o"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_glaze_image",
            "description": "Generate a photorealistic image of what the fired glaze looks like",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "composition_summary": {"type": "string"},
                },
                "required": ["description"],
            },
        },
    },
]
