# From https://github.com/ricequant/rqalpha/issues/5

def init(context):
  context.stocks = ['000300.XSHG', '000905.XSHG', '000012.XSHG']


def handle_bar(context, bar_dict):
  [hs, zz, gz] = context.stocks
  history20 = history(20, '1d', 'close')
  hsIncrease = history20[hs][-1] - history20[hs][0]
  zzIncrease = history20[zz][-1] - history20[zz][0]
  positions = context.portfolio.positions
  [hsQuality, zzQuality, gzQuality] = [positions[hs].quantity, positions[zz].quantity, positions[gz].quantity]
  if hsIncrease < 0 and zzIncrease < 0:
    if hsQuality > 0: order_target_percent(hs, 0)
    if zzQuality > 0: order_target_percent(zz, 0)
    order_target_percent(gz, 1)
  elif hsIncrease < zzIncrease:
    if hsQuality > 0: order_target_percent(hs, 0)
    if gzQuality > 0: order_target_percent(gz, 0)
    order_target_percent(zz, 1)
  else:
    if zzQuality > 0: order_target_percent(zz, 0)
    if gzQuality > 0: order_target_percent(gz, 0)
    order_target_percent(hs, 1)
  logger.info("positions hs300: " + str(hsQuality) + ", zz500: " + str(zzQuality) + ", gz: " + str(gzQuality))
