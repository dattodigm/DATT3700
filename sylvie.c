// --- 第一组：电机 A 与 LED 1 ---
const int M1_A = 25; const int M1_B = 26;
const int L1_R = 2;  const int L1_G = 4;  const int L1_B = 5;

// --- 第二组：电机 B 与 LED 2 ---
const int M2_A = 18; const int M2_B = 19;
const int L2_R = 12; const int L2_G = 13; const int L2_B = 14;

void setup() {
  // 初始化所有引脚为输出模式
  int pins[] = {M1_A, M1_B, M2_A, M2_B, L1_R, L1_G, L1_B, L2_R, L2_G, L2_B};
  for (int p : pins) pinMode(p, OUTPUT);
}

void loop() {
  // --- 动作 1：花 A 开（黄灯），花 B 关（无灯） ---
  // LED 1 调成黄色 (红+绿)
  digitalWrite(L1_R, HIGH); digitalWrite(L1_G, HIGH); digitalWrite(L1_B, LOW);
  digitalWrite(L2_R, LOW);  digitalWrite(L2_G, LOW);  digitalWrite(L2_B, LOW);

  digitalWrite(M1_A, HIGH); digitalWrite(M1_B, LOW);  // 电机 A 正转
  digitalWrite(M2_A, LOW);  digitalWrite(M2_B, HIGH); // 电机 B 反转
  delay(3000); // 维持 3 秒

  // --- 动作 2：全部停止（中间缓冲） ---
  digitalWrite(M1_A, LOW); digitalWrite(M1_B, LOW);
  digitalWrite(M2_A, LOW); digitalWrite(M2_B, LOW);
  delay(500);

  // --- 动作 3：花 A 关（无灯），花 B 开（青灯） ---
  // LED 2 调成青蓝色 (绿+蓝)
  digitalWrite(L1_R, LOW);  digitalWrite(L1_G, LOW);  digitalWrite(L1_B, LOW);
  digitalWrite(L2_R, LOW);  digitalWrite(L2_G, HIGH); digitalWrite(L2_B, HIGH);

  digitalWrite(M1_A, LOW);  digitalWrite(M1_B, HIGH); // 电机 A 反转
  digitalWrite(M2_A, HIGH); digitalWrite(M2_B, LOW);  // 电机 B 正转
  delay(3000);
}
