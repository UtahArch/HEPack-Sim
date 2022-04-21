# python run cheetah.py f1 f1 1024 1 &
# python run epic.py f1 f1 1024 1 &
# python run hyena.py f1 f1 1024 1 &
# python run hyena.py hyena f1 1024 1 &
# python run hyena.py hyena hyena 1024 1 &

rm -r data_gnmt/*/*
python run_cheetah.py  gnmt f1 f1  &
python run_cheetah.py  gnmt f1 hyena &
python run_epic.py  gnmt f1 f1 &
python run_epic.py  gnmt f1 hyena &
python run_hyena.py  gnmt f1 f1 &
python run_hyena.py  gnmt f1 hyena &
python run_hyena.py  gnmt opt f1 &
python run_hyena.py  gnmt opt hyena &
python run_ngraph.py gnmt &
wait