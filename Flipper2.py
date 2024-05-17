import requests
import tkinter as tk
from tkinter import ttk, scrolledtext, BooleanVar, StringVar
from datetime import datetime
from functools import lru_cache
import threading
from datetime import datetime, timezone


AUCTION_API_URL = "https://api.hypixel.net/skyblock/auctions"
KAT_API_URL = "https://sky.coflnet.com/api/kat/profit"
LOWEST_SUPPLY_API_URL = "https://sky.coflnet.com/api/auctions/supply/low"
ITEMS_API_URL = "https://sky.coflnet.com/api/items"

def increase_rarity(rarity):
    rarities = {
        "COMMON": "UNCOMMON",
        "UNCOMMON": "RARE",
        "RARE": "EPIC",
        "EPIC": "LEGENDARY",
        "LEGENDARY": "MYTHIC",
        "MYTHIC": "DIVINE",
        "DIVINE": "SPECIAL",
        "SPECIAL": "VERY SPECIAL"
    }
    return rarities.get(rarity, rarity)

def format_start_bid(start_bid):
    return '{:,.0f}'.format(start_bid)

def format_highest_bid(highest_bid):
    return '{:,.0f}'.format(highest_bid)

def format_end_time(end_time):
    return datetime.utcfromtimestamp(end_time / 1000).strftime('%Y-%m-%d %H:%M:%S')

def format_time_left(end_time):
    current_time = datetime.now(timezone.utc)
    end_time = datetime.fromtimestamp(end_time / 1000, timezone.utc)
    time_left = end_time - current_time

    weeks, days = divmod(time_left.days, 7)
    hours, seconds = divmod(time_left.seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    time_left_str = "Time Left: "
    if weeks:
        time_left_str += f"{weeks}w, "
    if days:
        time_left_str += f"{days}d, "
    if hours:
        time_left_str += f"{hours}h, "
    if minutes:
        time_left_str += f"{minutes}m, "
    time_left_str += f"{seconds}s."

    return time_left_str

MAX_CACHE_SIZE = 1000

def clean_item_lore(item_lore):
    cleaned_item_lore = ""
    i = 0
    while i < len(item_lore):
        if item_lore[i] == '§':
            i += 2
        else:
            cleaned_item_lore += item_lore[i]
            i += 1
    return cleaned_item_lore

def get_all_auction_data(search_keyword):
    all_auction_data = []
    page = 1
    while True:
        auction_data = query_auction_data(search_keyword, page)
        if auction_data:
            all_auction_data.extend(auction_data)
            page += 1
        else:
            break
    return all_auction_data

@lru_cache(maxsize=MAX_CACHE_SIZE)
def query_auction_data(search_keyword, page=1):
    try:
        response = requests.get(f"{AUCTION_API_URL}&page={page}")
        if response.status_code == 200:
            data = response.json()
            if data["success"]:
                auction_data = data["auctions"]
                return auction_data
            else:
                return None
        else:
            return None
    except Exception as e:
        return None

@lru_cache(maxsize=MAX_CACHE_SIZE)
def query_kat_profit_data():
    try:
        response = requests.get(KAT_API_URL)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return None
    except Exception as e:
        return None

@lru_cache(maxsize=MAX_CACHE_SIZE)
def update_items_data():
    try:
        response = requests.get(ITEMS_API_URL)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return None
    except Exception as e:
        return None

def query_items_data():
    updated_items_data = update_items_data()
    if updated_items_data:
        return updated_items_data

    try:
        response = requests.get(ITEMS_API_URL)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return None
    except Exception as e:
        return None

def query_lowest_supply_data():
    try:
        response = requests.get(LOWEST_SUPPLY_API_URL)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return None
    except Exception as e:
        return None

def combine_and_display_data():
    search_keyword = search_var.get()
    bin_filter_value = bin_filter.get()
    sort_option = sort_var.get()

    def process_data():
        current_tab = notebook.tab(notebook.select(), "text")
        if current_tab == "Hypixel Auction Search":
            process_hypixel_data()
        elif current_tab == "KAT Profit Data":
            process_kat_data()
        elif current_tab == "Lowest Supply Auctions":
            process_lowest_supply_auctions()

    data_processing_thread = threading.Thread(target=process_data)
    data_processing_thread.start()

    def process_hypixel_data():
        all_auction_data = get_all_auction_data(search_keyword)
        filtered_auctions = [auction for auction in all_auction_data if search_keyword.lower() in auction['item_name'].lower()]

        if bin_filter_value:
            filtered_auctions = [auction for auction in filtered_auctions if auction.get('bin', False)]
        else:
            filtered_auctions = [auction for auction in filtered_auctions if not auction.get('bin', False)]

        if sort_option == "lowest to highest price":
            sorted_auctions = sorted(filtered_auctions, key=lambda x: x.get('starting_bid', 0))
        elif sort_option == "highest to lowest price":
            sorted_auctions = sorted(filtered_auctions, key=lambda x: x.get('starting_bid', 0), reverse=True)
        elif sort_option == "ending soonest":
            sorted_auctions = sorted(filtered_auctions, key=lambda x: x['end'])

        result_text.config(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "Hypixel Auction Data:\n")
        for auction in sorted_auctions:
            item_name = auction['item_name']
            item_lore = clean_item_lore(auction.get('item_lore', 'N/A'))
            starting_bid = format_start_bid(auction.get('starting_bid', 0))
            highest_bid = format_highest_bid(auction.get('highest_bid_amount', 0))
            uuid = auction.get('uuid', 'N/A')
            auctioneer = auction.get('auctioneer', 'N/A')
            end_time = format_end_time(auction['end'])
            time_left = format_time_left(auction['end'])
            bin_value = auction.get('bin', 'N/A')

            result_text.insert(tk.END, f"Item: {item_name}\nItem Lore: {item_lore}\nStarting Bid: {starting_bid}\nHighest Bid: {highest_bid}\nUUID: {uuid}\nSeller: {auctioneer}\nEnd Time: {end_time}\n{time_left}\nBIN: {bin_value}\n\n------------------------------------------------------------\n\n")
        result_text.config(state=tk.DISABLED)

import tkinter as tk

class Item:
    def __init__(self, origin_auction_name, reference_auction, original_rarity, target_rarity, hours, material, amount, material_cost, kat_cost, median):
        self.origin_auction_name = origin_auction_name
        self.reference_auction = reference_auction
        self.original_rarity = original_rarity
        self.target_rarity = target_rarity
        self.hours = hours
        self.material = material
        self.amount = amount
        self.material_cost = material_cost
        self.kat_cost = kat_cost
        self.total_cost = material_cost + kat_cost
        self.median = median
        self.profit = self.calculate_profit()

    def calculate_profit(self):
        return self.median - self.total_cost

def format_number(number):
    if number >= 10**9:
        return f"{number / 10**9:.1f}b"
    elif number >= 10**6:
        return f"{number / 10**6:.1f}m"
    elif number >= 10**3:
        return f"{number / 10**3:.0f}k"
    else:
        return f"{number}"

def process_kat_data():
    kat_profit_data = query_kat_profit_data()
    items_data = query_items_data()  # Ensure you're using the latest items data

    if kat_profit_data and items_data:
        items = []

        for item in kat_profit_data:
            core_data = item.get("coreData", {})
            material_cost = item.get("materialCost", 0) + item.get("purchaseCost", 0)
            total_cost = core_data.get("cost", 0) + material_cost
            median = item.get("median", 0)
            new_item = Item(
                origin_auction_name=item.get("originAuctionName", "N/A"),
                reference_auction=item.get("referenceAuction", "N/A"),
                original_rarity=core_data.get("baseRarity", "N/A"),
                target_rarity=item.get("targetRarity", "N/A"),
                hours=core_data.get("hours", "N/A"),
                material=core_data.get("material", "N/A"),
                amount=core_data.get("amount", 0),
                material_cost=material_cost,
                kat_cost=core_data.get("cost", 0),
                median=median
            )
            items.append(new_item)

        sorted_items = sorted(items, key=lambda x: x.profit, reverse=True)

        result_text.config(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "KAT Profit Data:\n")

        for item in sorted_items:
            material_cost_formatted = format_number(item.material_cost)
            kat_cost_formatted = format_number(item.kat_cost)
            total_cost_formatted = format_number(item.total_cost)
            median_formatted = format_number(item.median)
            profit_formatted = format_number(item.profit)

            result_text.insert(tk.END, f"\nAuction Name: {item.origin_auction_name}\nReference Auction: {item.reference_auction}\n\nOriginal Rarity: {item.original_rarity}\nTarget Rarity: {item.target_rarity}\n\nTime: {item.hours} hours\nMaterial: {item.material}\nAmount: {item.amount}\n\nMaterial Cost (original pet + materials): {material_cost_formatted}\nKat Cost: {kat_cost_formatted}\nTotal Cost: {total_cost_formatted}\nMedian (How much you should be able to sell it for): {median_formatted}\n\nProfit: {profit_formatted}\n\n------------------------------------------------------------\n")
        
        result_text.config(state=tk.DISABLED)

# Example usage:
# process_kat_data()



def process_lowest_supply_auctions():
    sorted_items = [] 

    def update_result_text():
        nonlocal sorted_items 
        try:
            lowest_supply_data = query_lowest_supply_data()
            if lowest_supply_data:
                items_data = query_items_data()
                if items_data:
                    items_by_name = {item["tag"]: item["name"] for item in items_data}

                    items_with_margin = []
                    for item in lowest_supply_data:
                        item_id = item["tag"]
                        item_name = items_by_name.get(item_id, "Unknown Item")
                        lowest = item["lbinData"]["lowest"]
                        second_lowest = item["lbinData"]["secondLowest"]
                        margin = format(second_lowest - lowest, ",.0f")
                        real_margin = format(item["median"] - lowest, ",.0f")
                        median = format(item["median"], ",.0f")

                        items_with_margin.append({
                            "name": item_name,
                            "lowest": format(lowest, ",.0f"),
                            "second_lowest": format(second_lowest, ",.0f"),
                            "margin": margin,
                            "real_margin": real_margin,
                            "median": median
                        })

                    sorted_items = sorted(items_with_margin, key=lambda x: int(x["real_margin"].replace(",", "")), reverse=True)

                    result_text.delete(1.0, tk.END)
                    result_text.insert(tk.END, "Lowest Supply Auctions:\n")
                    for item in sorted_items:
                        result_text.insert(tk.END, f"Name: {item['name']},\nLowest: {item['lowest']}, Second Lowest: {item['second_lowest']},\nReal Margin: {item['real_margin']} (Median: {item['median']})\n\n")
                else:
                    result_text.delete(1.0, tk.END)
                    result_text.insert(tk.END, "Failed to fetch item data. Please check your connection.")
            else:
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, "Failed to fetch lowest supply data. Please check your connection.")
        except Exception as e:
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, f"An error occurred: {str(e)}")

    root.after(0, update_result_text)
    result_text.config(state=tk.DISABLED)

root = tk.Tk()
root.title("Hypixel & KAT Data Viewer")

notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)

hypixel_frame = ttk.Frame(notebook)
notebook.add(hypixel_frame, text="Hypixel Auction Search")

search_label = tk.Label(hypixel_frame, text="Enter a keyword to filter item names:")
search_label.grid(row=0, column=0)

search_var = StringVar()
search_entry = tk.Entry(hypixel_frame, textvariable=search_var)
search_entry.grid(row=0, column=1)

search_button = tk.Button(hypixel_frame, text="Search", command=combine_and_display_data)
search_button.grid(row=0, column=2)

bin_filter = BooleanVar()
bin_checkbox = tk.Checkbutton(hypixel_frame, text="Buy it now?", variable=bin_filter)
bin_checkbox.grid(row=0, column=3)

sort_var = StringVar(value="lowest to highest price")
sort_menu = tk.OptionMenu(hypixel_frame, sort_var, "lowest to highest price", "highest to lowest price", "ending soonest")
sort_menu.grid(row=0, column=4)

result_text = scrolledtext.ScrolledText(hypixel_frame, wrap=tk.WORD, width=60, height=20)
result_text.grid(row=1, columnspan=5)

kat_frame = ttk.Frame(notebook)
notebook.add(kat_frame, text="KAT Profit Data")

fetch_kat_button = tk.Button(kat_frame, text="Fetch KAT Profit Data", command=combine_and_display_data)
fetch_kat_button.pack()

lowest_supply_frame = ttk.Frame(notebook)
notebook.add(lowest_supply_frame, text="Lowest Supply Auctions")

fetch_lowest_supply_button = tk.Button(lowest_supply_frame, text="Fetch Lowest Supply Auctions", command=combine_and_display_data)
fetch_lowest_supply_button.pack()

root.mainloop()
