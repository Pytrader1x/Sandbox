import eikon as ek
import datetime
import asyncio

class EikonStreamingPrices:
    def __init__(self, app_key):
        self.app_key = app_key
        self.instruments = ["AUD=", "EUR="]
        self.bid_offer = {inst: [0.0, 0.0] for inst in self.instruments}
        ek.set_app_key(self.app_key)

    def display_refreshed_fields(self, streaming_price, instrument_name, fields):
        current_time = datetime.datetime.now().time()
        print(f"{current_time} - Refresh received for {instrument_name}: {fields}")
        self.update_bid_offer(instrument_name, fields)

    def display_updated_fields(self, streaming_price, instrument_name, fields):
        current_time = datetime.datetime.now().time()
        print(f"{current_time} - Update received for {instrument_name}: {fields}")
        self.update_bid_offer(instrument_name, fields)

    def display_status(self, streaming_price, instrument_name, status):
        current_time = datetime.datetime.now().time()
        print(f"{current_time} - Status received for {instrument_name}: {status}")

    def display_complete_snapshot(self, streaming_prices):
        current_time = datetime.datetime.now().time()
        print(f"{current_time} - StreamingPrice is complete. Full snapshot:")
        print(streaming_prices.get_snapshot())

    def update_bid_offer(self, instrument_name, fields):
        bid = fields.get('CF_BID', self.bid_offer[instrument_name][0])
        ask = fields.get('CF_ASK', self.bid_offer[instrument_name][1])
        self.bid_offer[instrument_name] = [bid, ask]
        self.print_bid_offer(instrument_name)

    def print_bid_offer(self, instrument_name):
        bid, ask = self.bid_offer[instrument_name]
        print(f"{instrument_name}: Bid = {bid}, Offer = {ask}")

    def start_streaming(self):
        streaming_prices = ek.StreamingPrices(
            instruments=self.instruments,
            fields=['CF_BID', 'CF_ASK'],
            on_refresh=self.display_refreshed_fields,
            on_update=self.display_updated_fields,
            on_status=self.display_status,
            on_complete=self.display_complete_snapshot
        )
        streaming_prices.open()

        # Keep the script running to receive streaming updates
        asyncio.get_event_loop().run_forever()

# Usage example
if __name__ == "__main__":
    app_key = "YOUR_EIKON_APP_KEY"  # Replace with your actual Eikon App Key
    streamer = EikonStreamingPrices(app_key)
    streamer.start_streaming()
