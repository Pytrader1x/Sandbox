class PositionManager:
    # Existing methods...

    def plot_trades(self, show_position_size=False, plot_levels=True):
        df = self.srf.df

        fig, ax1 = plt.subplots(figsize=(20, 10))

        ax1.plot(df['Close'], label='Close Price', color='black')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Price', color='black')
        ax1.tick_params(axis='y', labelcolor='black')

        ax2 = ax1.twinx()
        ax2.set_ylabel('Cumulative PnL', color='blue')
        ax2.tick_params(axis='y', labelcolor='blue')

        labels = []

        for i, trade in self.trade_history.iterrows():
            color = 'g' if trade['direction'] == 'long' else 'r'
            marker = '^' if trade['action'] == 'open' else 'v'
            label = f"{trade['direction'].capitalize()} {'Open' if trade['action'] == 'open' else 'Close'}"
            if label not in labels:
                labels.append(label)
                ax1.scatter(trade['datetime'], trade['entry_price'], color=color, marker=marker, label=label)
            else:
                ax1.scatter(trade['datetime'], trade['entry_price'], color=color, marker=marker)

        self.trade_history['cumulative_pnl'] = self.trade_history['realized_pnl'].cumsum()
        ax2.plot(self.trade_history['datetime'], self.trade_history['cumulative_pnl'], label='Cumulative PnL', color='blue')

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc=2)

        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        ax1.xaxis.set_minor_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        ax1.grid(True)

        plt.title('Trade Plotting')

        if plot_levels:
            # Integrate level plotting logic
            pivot_high_label, pivot_low_label = True, True
            for i in range(len(df)):
                if not np.isnan(df['pivot_high'].iloc[i]):
                    ax1.hlines(y=df['pivot_high'].iloc[i], xmin=df.index[i - self.srf.left_bars], xmax=df.index[i + self.srf.right_bars], color='red', linestyle='--', linewidth=0.8, alpha=0.7, label='Pivot High' if pivot_high_label else "")
                    pivot_high_label = False
                if not np.isnan(df['pivot_low'].iloc[i]):
                    ax1.hlines(y=df['pivot_low'].iloc[i], xmin=df.index[i - self.srf.left_bars], xmax=df.index[i + self.srf.right_bars], color='blue', linestyle='--', linewidth=0.8, alpha=0.7, label='Pivot Low' if pivot_low_label else "")
                    pivot_low_label = False

            # Plot confluence levels
            confluence_support_label = True
            for level, details in self.srf.support_levels.items():
                if details['count'] >= self.srf.min_confluence_count:
                    ax1.hlines(y=level, xmin=details['time'], xmax=df.index[-1], color='green', linestyle='-', linewidth=0.5 * details['count'], alpha=0.8, label='Confluence Support' if confluence_support_label else "")
                    confluence_support_label = False
            confluence_resistance_label = True
            for level, details in self.srf.resistance_levels.items():
                if details['count'] >= self.srf.min_confluence_count:
                    ax1.hlines(y=level, xmin=details['time'], xmax=df.index[-1], color='red', linestyle='-', linewidth=0.5 * details['count'], alpha=0.8, label='Confluence Resistance' if confluence_resistance_label else "")
                    confluence_resistance_label = False

        if show_position_size:
            # Create another subplot for showing position sizes
            fig, ax3 = plt.subplots(figsize=(20, 5))
            position_timeline_df = pd.DataFrame(self.position_timeline, columns=['datetime', 'position_size'])
            ax3.plot(position_timeline_df['datetime'], position_timeline_df['position_size'], label='Position Size', color='purple')
            ax3.set_ylabel('Position Size')
            ax3.legend()
            ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
            ax3.xaxis.set_minor_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
            plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
            ax3.grid(True)
            plt.title('Position Size Over Time')

        plt.show()
