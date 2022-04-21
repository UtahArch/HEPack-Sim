# python run cheetah.py f1 f1 1024 1 &
# python run epic.py f1 f1 1024 1 &
# python run hyena.py f1 f1 1024 1 &
# python run hyena.py hyena f1 1024 1 &
# python run hyena.py hyena hyena 1024 1 &

rm -r data_mobile/*/*
python run_cheetah.py mobile f1 f1 &
python run_cheetah.py mobile f1 hyena &
python run_epic.py mobile f1 f1 &
python run_epic.py mobile f1 hyena &
python run_hyena.py mobile f1 f1 &
python run_hyena.py mobile f1 hyena &
python run_hyena.py mobile opt f1 &
python run_hyena.py mobile opt hyena &
python run_ngraph.py mobile &
wait