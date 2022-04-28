# -*- coding: utf-8 -*-
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

from datetime import datetime

from fritzinfluxdb.common import grab

fritzbox_services = list()

fritzbox_services.append(
    {
        "name": "System Stats",
        "page": "ecoStat",
        "value_instances": {
            "cpu_temp": {
                "data_path": "data.cputemp.series.0.-1",
                "type": int
            },
            "cpu_utilization": {
                "data_path": "data.cpuutil.series.0.-1",
                "type": int
            },
            "ram_usage_fixed": {
                "data_path": "data.ramusage.series.0.-1",
                "type": int
            },
            "ram_usage_dynamic": {
                "data_path": "data.ramusage.series.1.-1",
                "type": int
            },
            "ram_usage_free": {
                "data_path": "data.ramusage.series.2.-1",
                "type": int
            }
        }
    })

fritzbox_services.append(
    {
        "name": "Energy Stats",
        "page": "energy",
        "value_instances": {
            "energy_consumption": {
                "data_path": "data.drain",
                "type": list,
                "next": {
                    # data struct type: dict
                    "type": int,
                    "tags_function": lambda data: {"name": data.get("name")},
                    "value_function": lambda data: data.get("actPerc"),
                    "exclude_filter_function": lambda data: "lan" in data.keys()
                }
            }
        }
    })

fritzbox_services.append(
    {
        "name": "System logs",
        "page": "log",
        "params": {
            "filter": 1
        },
        "track": True,
        "interval": 60,
        "value_instances": {
            "log_entry": {
                "data_path": "data.log",
                "type": list,
                "next": {
                    # data struct type: list
                    "type": str,
                    "tags": {
                        "log_type": "System"
                    },
                    "timestamp_function": lambda data:
                        datetime.strptime(f'{data[0]} {data[1]}', '%d.%m.%y %H:%M:%S'),
                    "value_function": lambda data: data[2],
                    "tags_function": None
                }
            }
        }
    })

fritzbox_services.append(
    {
        "name": "Internet connection logs",
        "page": "log",
        "params": {
            "filter": 2
        },
        "track": True,
        "interval": 61,
        "value_instances": {
            "log_entry": {
                "data_path": "data.log",
                "type": list,
                "next": {
                    # data struct type: list
                    "type": str,
                    "tags": {
                        "log_type": "Internet connection"
                    },
                    "timestamp_function": lambda data:
                        datetime.strptime(f'{data[0]} {data[1]}', '%d.%m.%y %H:%M:%S'),
                    "value_function": lambda data: data[2],
                    "tags_function": None
                }
            }
        }
    })

fritzbox_services.append(
    {
        "name": "Telephony logs",
        "page": "log",
        "params": {
            "filter": 3
        },
        "track": True,
        "interval": 62,
        "value_instances": {
            "log_entry": {
                "data_path": "data.log",
                "type": list,
                "next": {
                    # data struct type: list
                    "type": str,
                    "tags": {
                        "log_type": "Telephony"
                    },
                    "timestamp_function": lambda data:
                        datetime.strptime(f'{data[0]} {data[1]}', '%d.%m.%y %H:%M:%S'),
                    "value_function": lambda data: data[2],
                    "tags_function": None
                }
            }
        }
    })

fritzbox_services.append(
    {
        "name": "WLAN logs",
        "page": "log",
        "params": {
            "filter": 4
        },
        "track": True,
        "interval": 63,
        "value_instances": {
            "log_entry": {
                "data_path": "data.log",
                "type": list,
                "next": {
                    # data struct type: list
                    "type": str,
                    "tags": {
                        "log_type": "WLAN"
                    },
                    "timestamp_function": lambda data:
                        datetime.strptime(f'{data[0]} {data[1]}', '%d.%m.%y %H:%M:%S'),
                    "value_function": lambda data: data[2],
                    "tags_function": None
                }
            }
        }
    })

fritzbox_services.append(
    {
        "name": "USB Devices logs",
        "page": "log",
        "params": {
            "filter": 5
        },
        "track": True,
        "interval": 64,
        "value_instances": {
            "log_entry": {
                "data_path": "data.log",
                "type": list,
                "next": {
                    # data struct type: list
                    "type": str,
                    "tags": {
                        "log_type": "USB Devices"
                    },
                    "timestamp_function": lambda data:
                    datetime.strptime(f'{data[0]} {data[1]}', '%d.%m.%y %H:%M:%S'),
                    "value_function": lambda data: data[2],
                    "tags_function": None
                }
            }
        }
    })


extract_single_host = {
    # data struct type: dict
    "type": str,
    "tags_function": lambda data: {
        "name": data.get("name"),
        "mac": data.get("mac"),
        "type": data.get("type"),
        "parent": data.get("parent", dict()).get("name"),
        "port": data.get("port"),
        "ipv4": data.get("ipv4", dict()).get("ip"),
        "ipv4_last_used": data.get("ipv4", dict()).get("lastused", 0),

        # need this construct to deal with an empty "properties" list
        "additional_text": (lambda x:
                            x[0].get("txt", "") if len(x) != 0 else ""
                            )(
            data.get("properties", [{"txt": ""}])
        )
    },
    "value_function": lambda data: data.get("UID"),
    "exclude_filter_function": None
}

# every 2 minutes
fritzbox_services.append(
    {
        "name": "Active network hosts",
        "page": "netDev",
        "params": {
            "useajax": 1,
            "xhrId": "all",
            "xhr": 1,
            "initial": True
        },
        "interval": 120,
        "value_instances": {
            "active_host": {
                "data_path": "data.active",
                "type": list,
                "next": extract_single_host
            },
            "num_active_host": {
                "type": int,
                "value_function": lambda data: len(data.get("data", {}).get("active", [])),
            }
        }
    }
)

# every 10 minutes
fritzbox_services.append({
        "name": "Passive network hosts",
        "page": "netDev",
        "params": {
            "useajax": 1,
            "xhrId": "cleanup",
            "xhr": 1,
        },
        "interval": 600,
        "value_instances": {
            "passive_host": {
                "data_path": "data.passive",
                "type": list,
                "next": extract_single_host
            },
            "num_passive_host": {
                "type": int,
                "value_function": lambda data: len(data.get("data", {}).get("passive", [])),
            }
        }
    }
)

fritzbox_services.append({
        # ToDo:
        #   * Dashboard
        "name": "VPN Users",
        "page": "shareVpn",
        "params": {
            "xhrId": "all",
            "xhr": 1,
        },
        "value_instances": {
            "myfritz_host_name": {
                "data_path": "data.vpnInfo.server",
                "type": str
            },
            "vpn_user": {
                "data_path": "data.vpnInfo.userConnections",
                "type": dict,
                "next": {
                    "type": str,
                    "value_function": lambda data: data.get("name"),
                    "tags_function": lambda data: {
                        "connected": data.get("connected"),
                        "active": data.get("active"),
                        "virtual_address": data.get("virtualAddress"),
                        "remote_address": data.get("address"),
                    }
                }
            },
            "num_active_vpn_users": {
                "type": int,
                "value_function": (lambda data:
                                   len(
                                       [x for x in grab(data, "data.vpnInfo.userConnections", fallback=dict()).values()
                                        if x.get("connected") is True]
                                   )
                                   ),

            }
        }
    }
)

fritzbox_services.append({
        # ToDo:
        #   * Dashboard
        "name": "DSL Info",
        "page": "dslOv",
        "params": {
            "xhrId": "all",
            "xhr": 1,
            "useajax": 1
        },
        "interval": 600,
        "value_instances": {
            "dsl_line_length": {
                "data_path": "data.connectionData.lineLength",
                "type": int
            },
            "dsl_dslam_vendor": {
                "data_path": "data.connectionData.dslamId",
                "type": str
            },
            "dsl_dslam_sw_versino": {
                "data_path": "data.connectionData.version",
                "type": str
            },
            "dsl_line_mode": {
                "data_path": "data.connectionData.line.0.mode",
                "type": str
            }
        }
    }
)
