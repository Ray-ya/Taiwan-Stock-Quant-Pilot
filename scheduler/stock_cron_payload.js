const res = await exec({
  command: 'python C:\\Users\\globa\\.openclaw\\workspace\\Taiwan-Stock-Quant-Pilot\\scheduler\\daily_runner.py SCHEDULED_0800'
});
return { ok: true, output: res };
