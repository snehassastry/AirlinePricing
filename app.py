from flask import Flask, render_template, request, stream_with_context, Response
import matplotlib.pyplot as plt
import io
import base64
import numpy as np
from scipy.stats import binom
import time

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template("index.html", form_values={}, summary_table=None)

@app.route('/stream', methods=['POST'])
def stream():
    form_values = {key: request.form[key] for key in request.form}

    @stream_with_context
    def generate():
        yield f"data: <b>⏳ Starting optimization...</b><br>\n"
        time.sleep(0.5)

        time_steps = int(form_values.get("time_steps"))
        n_seats_coach = int(form_values.get("n_seats_coach"))
        overbook_limit = int(form_values.get("overbook_coach"))
        n_seats_first = int(form_values.get("n_seats_first"))
        discount = 1 / (1 + float(form_values.get("discount")) / 365)

        showup_prob_coach = float(form_values.get("showup_prob_coach"))
        showup_prob_first = float(form_values.get("showup_prob_first"))

        price_coach = [int(form_values.get("price_coach_low")), int(form_values.get("price_coach_high"))]
        prob_coach = [float(form_values.get("prob_coach_low")), float(form_values.get("prob_coach_high"))]

        price_first = [int(form_values.get("price_first_low")), int(form_values.get("price_first_high"))]
        prob_first = [float(form_values.get("prob_first_low")), float(form_values.get("prob_first_high"))]

        coach_price_boost = float(form_values.get("coach_price_boost"))
        cost_upgrade = float(form_values.get("cost_upgrade"))
        cost_off = float(form_values.get("cost_off"))

        apply_seasonality = form_values.get("apply_seasonality") == "True"
        has_option_to_not_sell = form_values.get("has_option_to_not_sell") == "True"

        V_dict = {}
        for ob in range(0, overbook_limit + 1):  # Start from 0 instead of 1
            yield f"data: ⏳ Calculating overbook policy for {ob} seats...<br>\n"
            V, _ = policy(ob, time_steps, n_seats_coach, n_seats_first, discount,
                          showup_prob_coach, showup_prob_first,
                          price_coach, prob_coach, price_first, prob_first,
                          coach_price_boost, cost_upgrade, cost_off,
                          apply_seasonality, has_option_to_not_sell)
            V_dict[ob] = V[0, 0, 0]
            time.sleep(0.2)

        best = max(V_dict, key=V_dict.get)
        best_val = V_dict[best]
        base_val = V_dict[0]
        improvement = ((best_val - base_val) / base_val) * 100 if base_val != 0 else 0

        result_msg = (f"✅ Best overbook policy: {best} seats with expected value ${best_val:,.2f} <br>"
                      f"📈 Improvement from 0 overbooked seats: {improvement:.2f}%")

        fig, ax = plt.subplots()
        ax.plot(list(V_dict.keys()), list(V_dict.values()), marker='o')
        ax.set_xlabel('Allowed Coach Overbook')
        ax.set_ylabel('Expected Present Value')
        ax.set_title('Expected Present Value vs Overbook Coach')
        ax.grid(True)
        graph_url = convert_plot_to_base64(fig)

        yield f"data: <hr><b>{result_msg}</b><br><img src='{graph_url}' class='plot'><br>\n"
        yield "data: [DONE]\n\n"

    return Response(generate(), mimetype='text/event-stream')

def policy(overbooked_seats, time_steps, n_coach, n_first, discount,
           showup_prob_coach, showup_prob_first,
           price_coach, prob_coach, price_first, prob_first,
           coach_price_boost, cost_upgrade, cost_off,
           apply_seasonality, has_option_to_not_sell):

    N_COACH = n_coach + overbooked_seats
    V = np.zeros((time_steps+1, N_COACH+1, n_first+1))
    U = np.zeros((time_steps+1, N_COACH+1, n_first+1))

    for c in range(N_COACH+1):
        for f in range(n_first+1):
            exp_cost = 0
            for i in range(n_coach+1, c+1):
                for j in range(f+1):
                    extra = max(i - n_coach, 0)
                    upgrades = min(n_first - j, extra)
                    cost = upgrades * cost_upgrade + (extra - upgrades) * cost_off
                    prob = binom.pmf(i, c, showup_prob_coach) * binom.pmf(j, f, showup_prob_first)
                    exp_cost += cost * prob
            V[time_steps, c, f] = -exp_cost
            U[time_steps, c, f] = -1

    for t in reversed(range(time_steps)):
        for c in range(N_COACH+1):
            for f in range(n_first+1):
                profits = []
                for pc in range(2):
                    for pf in range(2):
                        ep = 0
                        for sc in range(2):
                            for sf in range(2):
                                prob_c = prob_coach[pc]
                                prob_f = prob_first[pf]
                                if apply_seasonality:
                                    prob_c *= (0.75 + t / 730)
                                    prob_f *= (0.75 + t / 730)
                                if f == n_first:
                                    prob_c += coach_price_boost
                                    prob_f = 0
                                if c == N_COACH:
                                    prob_c = 0
                                pc_prob = prob_c if sc else 1 - prob_c
                                pf_prob = prob_f if sf else 1 - prob_f
                                prob = pc_prob * pf_prob
                                next_c, next_f = min(c+sc, N_COACH), min(f+sf, n_first)
                                reward = sc * price_coach[pc] + sf * price_first[pf]
                                future = V[t+1, next_c, next_f]
                                ep += prob * (reward + discount * future)
                        profits.append(ep)
                if has_option_to_not_sell:
                    for pf in range(2):
                        ep = 0
                        for sf in range(2):
                            prob_f = prob_first[pf]
                            if f == n_first:
                                prob_f = 0
                            if apply_seasonality:
                                prob_f *= (0.75 + t / 730)
                            pf_prob = prob_f if sf else 1 - prob_f
                            next_f = min(f+sf, n_first)
                            reward = sf * price_first[pf]
                            future = V[t+1, c, next_f]
                            ep += pf_prob * (reward + discount * future)
                        profits.append(ep)
                V[t, c, f] = max(profits)
                U[t, c, f] = np.argmax(profits)
    return V, U

def convert_plot_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    return f"data:image/png;base64,{base64.b64encode(buf.read()).decode('utf-8')}"

def build_summary_table(form):
    html = "<table class='summary-table'><tr><th>Parameter</th><th>Value</th></tr>"
    for key, val in form.items():
        html += f"<tr><td>{key.replace('_',' ').title()}</td><td>{val}</td></tr>"
    html += "</table>"
    return html

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

