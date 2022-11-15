# python run cheetah.py f1 f1 1024 1 &
# python run epic.py f1 f1 1024 1 &
# python run hyena.py f1 f1 1024 1 &
# python run hyena.py hyena f1 1024 1 &
# python run hyena.py hyena hyena 1024 1 &

# rm -r data_mobile/*/*

# for pack in epic cheetah
# do
#     for n in 16 4 1
#     do
#         python run_${pack}.py mobile f1 f1 ${n} &
#         python run_${pack}.py mobile f1 hyena ${n} &
#     done
#     wait
# done

# for n in 16 4 1
# do
#     python run_hyena.py  mobile f1 f1 ${n} &
#     python run_hyena.py  mobile f1 hyena ${n} &
#     python run_hyena.py  mobile opt f1 ${n} &
#     python run_hyena.py  mobile opt hyena ${n} &
#     wait
# done

# python run_ngraph.py mobile

rm -rf data_mobile/*/*

for pack in epic cheetah
do
    # for n in 16 4 1
    for n in 1
    do
        python run_${pack}.py mobile f1 f1 ${n} &
        python run_${pack}.py mobile f1 hyena ${n} &
    done
    # wait
done

# for n in 16 4 1
for n in 1
do
    python run_hyena.py  mobile f1 f1 ${n} &
    python run_hyena.py  mobile f1 hyena ${n} &
    # wait
done
wait