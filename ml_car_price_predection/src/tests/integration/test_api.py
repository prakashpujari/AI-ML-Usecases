from predict_api import info, predict, PredictRequest

print('INFO:', info())
req = PredictRequest(year=2015, mileage=50000, brand='Ford', condition='Good', engine_size=1.6, transmission='automatic')
print('PREDICT:', predict(req))
