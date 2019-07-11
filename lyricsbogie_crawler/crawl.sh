#!/bin/bash
#SBATCH -A research
#SBATCH -n 10
#SBATCH --qos=medium
#SBATCH -p long
#SBATCH --gres=gpu:0
#SBATCH --mem-per-cpu=3G
#SBATCH --time=4-00:00:00
source /home/$USER/lyricsbogie/bin/activate
export dir="/home/priyansh.agrawal/lyricsbogie/crawler"
cd $dir
#mkdir $dir/album_output
scrapy crawl songs_by_genre -o genre_output/data.jl --logfile=genre_output/output.log --loglevel=INFO 
