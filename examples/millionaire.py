from pymongo import MongoClient
from bitcoin_price_prediction.bayesian_regression import *
import warnings
import pickle


client = MongoClient()
database = client['stock']
collection = database['x_daily']
collection = database['svxy_intra']

warnings.filterwarnings(action="ignore", module="scipy", message="^internal gelsd")
np.seterr(divide='ignore', invalid='ignore')

# Retrieve price, v_ask, and v_bid data points from the database.
prices = []
dates =[]
#v_ask = []
#v_bid = []
#num_points = 777600
#for doc in collection.find().limit(num_points):
for doc in collection.find():
    prices.append(doc['close'])
    dates.append(doc['date'])
    #v_ask.append(doc['v_ask'])
    #v_bid.append(doc['v_bid'])

prices = prices[::-1]
dates = dates[::-1]

# Divide prices into three, roughly equal sized, periods:
# prices1, prices2, and prices3.
[prices1, prices2, prices3] = np.array_split(prices, 3)
[dates1, dates2, dates3] = np.array_split(dates, 3)

# Divide v_bid into three, roughly equal sized, periods:
# v_bid1, v_bid2, and v_bid3.
#[v_bid1, v_bid2, v_bid3] = np.array_split(v_bid, 3)

# Divide v_ask into three, roughly equal sized, periods:
# v_ask1, v_ask2, and v_ask3.
#[v_ask1, v_ask2, v_ask3] = np.array_split(v_ask, 3)
def make_model():
    # Use the first time period (prices1) to generate all possible time series of
    # appropriate length (180, 360, and 720).
    timeseries180 = generate_timeseries(prices1, 5)
    timeseries360 = generate_timeseries(prices1, 25)
    timeseries720 = generate_timeseries(prices1, 50)

    # Cluster timeseries180 in 100 clusters using k-means, return the cluster
    # centers (centers180), and choose the 20 most effective centers (s1).
    centers180 = find_cluster_centers(timeseries180, 100)
    s1 = choose_effective_centers(centers180, 20)

    centers360 = find_cluster_centers(timeseries360, 100)
    s2 = choose_effective_centers(centers360, 20)

    centers720 = find_cluster_centers(timeseries720, 100)
    s3 = choose_effective_centers(centers720, 20)

    # Use the second time period to generate the independent and dependent
    # variables in the linear regression model:
    # Δp = w0 + w1 * Δp1 + w2 * Δp2 + w3 * Δp3 + w4 * r.
    Dpi_r, Dp = linear_regression_vars(prices2, s1, s2, s3)

    # Find the parameter values w (w0, w1, w2, w3, w4).
    w = find_parameters_w(Dpi_r, Dp)

    # Predict average price changes over the third time period.
    dps = predict_dps(prices3, s1, s2, s3, w)
    return dps
# What's your 'Fuck You Money' number?

dps = make_model()

# file_dps = open('dps.obj', 'w')
# pickle.dump(dps, file_dps)


with open('dps_svxy_intra.pickle', 'wb') as f:
    pickle.dump(dps, f)


# file_prices3 = open('prices3.obj', 'w')
# pickle.dump(prices3, file_prices3)
#
# file_dates3 = open('dates3.obj', 'w')
# pickle.dump(dates3, file_dates3)

# for i in range(1):
#     bank_balance = evaluate_performance(prices3, dates3, dps, t=0.001, step=1)
#     print(bank_balance)
