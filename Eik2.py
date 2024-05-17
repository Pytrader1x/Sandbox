import eikon as ek
import time

class pricing:
    def __init__(self):
        self.major_ccys = ["AUDUSD", "EURUSD", "GBPUSD", "USDJPY", "NZDUSD", "USDCAD", "USDCHF", "USDSGD", "USDNOK"]
        self.bid_offer = {k: [0.0, 0.0] for k in self.major_ccys}

class eikon_pricing:
    def __init__(self, pricing_obj, app_key):
        self.pricing_obj = pricing_obj
        self.ccys = self.pricing_obj.major_ccys
        self.app_key = app_key

    def create_rics(self):
        self.rics = [f"{ccy[:3]}{ccy[3:]}=R" for ccy in self.ccys]

    def on_update(self, upd):
        try:
            ric = upd['ric']
            ccy = ric[:6]
            self.pricing_obj.bid_offer[ccy][0] = upd['BID']
            self.pricing_obj.bid_offer[ccy][1] = upd['ASK']
            print(f"{ccy}: Bid - {self.pricing_obj.bid_offer[ccy][0]}, Offer - {self.pricing_obj.bid_offer[ccy][1]}")
        except Exception as e:
            print(f"Error processing update: {e}")

    def run(self):
        ek.set_app_key(self.app_key)

        self.create_rics()
        print("Created list of RICs")

        try:
            ek.streaming.StreamingPrices(self.on_update, self.rics, ['BID', 'ASK'])
            time.sleep(1)  # Delay to ensure connection before checking for updates
            while True:
                time.sleep(1)  # Keep the script running to receive updates
        except ek.EikonError as e:
            print(f"Eikon Error: {e}")

def main():
    pricing_obj = pricing()
    app_key = "YOUR_APP_KEY"  # Replace with your Eikon app key

    eikon_pricer = eikon_pricing(pricing_obj, app_key)
    eikon_pricer.run()

if __name__ == "__main__":
    main()
