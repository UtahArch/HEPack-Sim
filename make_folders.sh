for bench in resnet gnmt mobile resnet20
do
    for pack in ngraphplus ngraph
    do
        for batch in 1 16 32 64 512
        do
            mkdir -p "data_${bench}/${pack}_${batch}_1024"
        done
    done
done

# for bench in resnet gnmt mobile
# do
#     for pack in hyenaplus
#     do
#         for batch in 1 16 32
#         do
#             mkdir -p "data_${bench}/${pack}_${batch}_f1_f1_1024"
#             mkdir -p "data_${bench}/${pack}_${batch}_f1_hyena_1024"
#         done
#     done
# done

for bench in resnet gnmt mobile resnet20
do
    for pack in cheetah epic hyena channel
    do
        for arch in f1 hyena
        do
            mkdir -p "data_${bench}/${pack}_f1_${arch}_1024"
        done
    done
done