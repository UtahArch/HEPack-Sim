# for network in mobile resnet gnmt
# do
#     rm -rf data_${network}/*/*
# done

# for network in mobile resnet gnmt
# do
#     # python run_ngraph.py ${network} 1 &
#     for pack in hyena epic cheetah channel
#     do
#         for n in 1
#         do
#             python run_${pack}.py ${network} f1 f1 ${n} &
#             python run_${pack}.py ${network} f1 hyena ${n} &
#         done    
#     done
#     wait
# done
# wait

for network in mobile resnet gnmt
do
    rm -rf data_${network}/ngraph*/*
    rm -rf data_${network}/hyenaplus*/*
done

for network in mobile resnet gnmt
do
    for batch in 1 16 32 64 512
    do
        python run_ngraphplus.py ${network} ${batch} 1 &
        python run_ngraph.py     ${network} ${batch} 1 &
    done
    wait
done
wait