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
        self.rics = [f"{ccy}=X" for ccy in self.ccys]

    def processMessage(self, msg):
        try:
            for ric, data in msg.items():
                if ric.startswith('Error'):
                    print(f"Error: {data}")
                else:
                    ccy = ric.split('=')[0]
                    self.pricing_obj.bid_offer[ccy][0] = data['BID']
                    self.pricing_obj.bid_offer[ccy][1] = data['ASK']
        except Exception as e:
            print(f"Error processing message: {e}")

    def run(self):
        ek.set_app_key(self.app_key)

        self.create_rics()
        print("Created list of RICs")

        fields = ['BID', 'ASK']

        while True:
            try:
                data = ek.get_data(self.rics, fields)
                self.processMessage(data)

                for ccy in self.ccys:
                    bid, offer = self.pricing_obj.bid_offer[ccy]
                    print(f"{ccy}: Bid - {bid}, Offer - {offer}")

                time.sleep(1)  # Wait for 1 second before the next update
            except ek.EikonError as e:
                print(f"Eikon Error: {e}")

def main():
    pricing_obj = pricing()
    app_key = "YOUR_APP_KEY"  # Replace with your Eikon app key

    eikon_pricer = eikon_pricing(pricing_obj, app_key)
    eikon_pricer.run()

if __name__ == "__main__":
    main()
