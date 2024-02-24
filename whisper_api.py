import wave
import struct
import math
import os
import shutil
import numpy as np
from openai import OpenAI

# API key を設定
client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
)


# API制限25MB用に加工準備
# ===================================================================

# 繰り返し作業用に事前に削除
if os.path.exists("./wave_split"):
    shutil.rmtree("./wave_split")

# 読み込むwaveファイル名
f_name = input("ファイル名を入力（wavのみ。拡張子不要）: ")

# 切り取り時間[sec]
cut_time = 3 * 60

# 保存するフォルダの作成
file = os.path.exists("wave_split")
if file == False:
    os.mkdir("wave_split")


def wav_cut(filename, time):

    # ファイルを読み出し
    wavf = filename + '.wav'
    wr = wave.open(wavf, 'r')

    # waveファイルが持つ性質を取得
    ch = wr.getnchannels()           # オーディオチャンネル数（モノラルなら 1 、ステレオなら 2 ）を返します。
    width = wr.getsampwidth()        # サンプルサイズをバイト数で返します。
    fr = wr.getframerate()           # サンプリングレートを返します。
    fn = wr.getnframes()             # オーディオフレーム数を返します。
    total_time = 1.0 * fn / fr       # 曲の長さ
    integer = math.floor(total_time)  # 曲の長さから小数点以下を切り捨てて整数の秒数に修正
    t = int(time)                    # 切り分けする秒数[sec]
    frames = int(ch * fr * t)        # 切り分けした秒数におけるオーディオフレーム数
    num_cut = int(integer//t + 1)    # 切り分け出力する数。末尾のオーディオフレームを追加するために+1としている

    # 確認用
    print("Channel: ", ch)
    print("Sample width: ", width)
    print("Frame Rate: ", fr)
    print("Frame num: ", fn)
    print("Params: ", wr.getparams())
    print("Total time: ", total_time)
    print("Total time(integer)", integer)
    print("Time: ", t)
    print("Frames: ", frames)
    print("Number of cut: ", num_cut)

    # waveの実データを取得し、数値化
    data = wr.readframes(wr.getnframes())
    wr.close()
    X = np.frombuffer(data, dtype=np.int16)
    print(X)

    for i in range(num_cut):
        print("No.", i+1)
        # 出力データを生成
        outf = 'wave_split/' + str(i+1) + '.wav'
        start_cut = i*frames
        end_cut = i*frames + frames
        print("Start Cut", start_cut)
        print("End Cut", end_cut)
        Y = X[start_cut:end_cut]
        outd = struct.pack("h" * len(Y), *Y)

        # 書き出し
        ww = wave.open(outf, 'w')
        ww.setnchannels(ch)
        ww.setsampwidth(width)
        ww.setframerate(fr)
        ww.writeframes(outd)
        ww.close()


# 実行
wav_cut(f_name, cut_time)


# Whisper API へデータの受け渡し
# ===================================================================

# 保存するフォルダの作成
file = os.path.exists("transcript_output")
if file == False:
    os.mkdir("transcript_output")

# 読み込む音声ファイルを取得
read_list = os.listdir("./wave_split")
file_list = list(range(1, len(read_list)+1))

# Whisper APIで文字起こししてテキストファイルへ書き込み
with open(f"./transcript_output/transcript_from_{f_name}.txt", mode="w", encoding="utf-8_sig") as f:

    for file_path in file_list:
        print(file_path, "is reading...")
        audio_file = open(f"./wave_split/{file_path}.wav", "rb")
        transcript = client.audio.transcriptions.create(
            model = "whisper-1",
            file = audio_file,
            response_format="text"
        )
        print(transcript)

        # テキストファイルへ書き込み
        wave_time = str(file_path*3-3) + "min.~" + str(file_path*3) + "min."

        f.write(str(file_path)+".wav 内容")
        f.write("\n")
        f.write(wave_time)
        f.write("\n")
        f.write(str(transcript))
        f.write("\n\n")
