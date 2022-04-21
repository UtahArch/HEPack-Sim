# python run cheetah.py f1 f1 1024 1 &
# python run epic.py f1 f1 1024 1 &
# python run hyena.py f1 f1 1024 1 &
# python run hyena.py hyena f1 1024 1 &
# python run hyena.py hyena hyena 1024 1 &

rm -r data_resnet/*/*
python run_cheetah.py resnet f1 f1 &
python run_cheetah.py resnet f1 hyena &
python run_epic.py resnet f1 f1 &
python run_epic.py resnet f1 hyena &
python run_hyena.py resnet f1 f1 &
python run_hyena.py resnet f1 hyena &
python run_hyena.py resnet opt f1 &
python run_hyena.py resnet opt hyena &
python run_ngraph.py resnet &
wait