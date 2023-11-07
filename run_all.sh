# python run cheetah.py f1 f1 1024 1 &
# python run epic.py f1 f1 1024 1 &
# python run hyena.py f1 f1 1024 1 &
# python run hyena.py hyena f1 1024 1 &
# python run hyena.py hyena hyena 1024 1 &

# rm -r data_resnet/*/*

# for y in 16 4 1
# do
#     python run_cheetah.py resnet f1 f1 ${y} &
#     python run_cheetah.py resnet f1 hyena ${y} &
#     python run_epic.py resnet f1 f1 ${y} &
#     python run_epic.py resnet f1 hyena ${y} &
#     python run_hyena.py resnet f1 f1 ${y} &
#     python run_hyena.py resnet f1 hyena ${y} &
#     python run_hyena.py resnet opt f1 ${y} &
#     python run_hyena.py resnet opt hyena ${y} &s
#     wait
# done
# python run_ngraph.py resnet
for network in mobile resnet gnmt
do
    rm -rf data_${network}/*/*
done

for network in mobile resnet gnmt
do
    for pack in hyena hyena_new epic cheetah
    do
        for n in 1
        do
            python run_${pack}.py resnet f1 f1 ${n} &
            python run_${pack}.py resnet f1 hyena ${n} &
        done    
    done
    wait
done
wait