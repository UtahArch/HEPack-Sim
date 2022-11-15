
# for d in */ ; 
# do
#     for y in 1024 4096 16384
#     do
#         echo "$d"
#     done
# done

for bench in resnet gnmt mobile
do
    for pack in cheetah epic hyena hyenaV2
    do
        for arch in f1 hyena
        do
            mkdir -p "data_${bench}/${pack}_f1_${arch}_1024"
        done
    done
done

# for name in resnet gnmt mobile
# do
#     mkdir "data_${name}"
#     for d in data/* ; 
#     do
#         for y in 1024 4096 16384
#         do
#             mkdir "${d/data/"data_${name}"}_${y}"
#         done
#     done
# done