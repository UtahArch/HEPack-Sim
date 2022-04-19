# python run cheetah.py f1 f1 1024 1 &
# python run epic.py f1 f1 1024 1 &
# python run hyena.py f1 f1 1024 1 &
# python run hyena.py hyena f1 1024 1 &
# python run hyena.py hyena hyena 1024 1 &

rm -r data/*/*
python run_cheetah.py f1 f1 1024 1 &
python run_cheetah.py f1 hyena 1024 1 &
python run_epic.py f1 f1 1024 1 &
python run_epic.py f1 hyena 1024 1 &
python run_hyena.py f1 f1 1024 1 &
python run_hyena.py f1 hyena 1024 1 &
python run_hyena.py opt f1 1024 1 &
python run_hyena.py opt hyena 1024 1 &
wait