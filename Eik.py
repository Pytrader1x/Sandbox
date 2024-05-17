import eikon as ek
import time

class EikonPricingStreamer:
    def __init__(self, app_key):
        self.app_key = app_key
        self.major_ccys = ["AUDUSD", "EURUSD", "GBPUSD", "USDJPY", "NZDUSD", "USDCAD", "USDCHF", "USDSGD", "USDNOK"]
        self.bid_offer = {ccy: [0.0, 0.0] for ccy in self.major_ccys}
        ek.set_app_key(self.app_key)
        self.streaming_session = ek.StreamingSession(self._on_update)

    def _on_update(self, update):
        for ccy in self.major_ccys:
            if ccy in update:
                bid = update[ccy].get('BID', self.bid_offer[ccy][0])
                ask = update[ccy].get('ASK', self.bid_offer[ccy][1])
                self.bid_offer[ccy] = [bid, ask]
                self.print_bid_offer(ccy)

    def start_streaming(self):
        instruments = [ccy + "=R" for ccy in self.major_ccys]
        fields = ["BID", "ASK"]
        self.streaming_session.open(instruments, fields)
        print("Streaming started...")

    def print_bid_offer(self, ccy):
        prices = self.bid_offer[ccy]
        print(f"{ccy}: Bid = {prices[0]}, Offer = {prices[1]}")

# Usage example
if __name__ == "__main__":
    app_key = "YOUR_EIKON_APP_KEY"  # Replace with your actual Eikon App Key
    pricing_streamer = EikonPricingStreamer(app_key)
    pricing_streamer.start_streaming()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Streaming stopped.")
        pricing_streamer.streaming_session.close()
