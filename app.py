from flask import Flask, render_template, request
import matplotlib.pyplot as plt
import io
import base64
import numpy as np

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    graph_url = None
    form_values = {}

    if request.method == 'POST':
        form_values = {key: request.form[key] for key in request.form}

        # Dummy plot for testing
        x = np.linspace(0, int(form_values.get('time_steps', 365)))
        y = np.sin(x / 20) * 100 + 500

        fig, ax = plt.subplots()
        ax.plot(x, y)
        ax.set_title("Test Graph")
        ax.set_xlabel("Time")
        ax.set_ylabel("Value")

        result = f"Max Y Value: {np.max(y):.2f}"
        graph_url = convert_plot_to_base64(fig)

    return render_template("index.html", result=result, graph_url=graph_url, form_values=form_values)

def convert_plot_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode('utf-8')
    return f'data:image/png;base64,{encoded}'

if __name__ == '__main__':
    app.run(debug=True)
