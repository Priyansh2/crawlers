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
mkdir $dir/album_output
mkdir $dir/movie_output
mkdir $dir/genre_output
scrapy crawl album_songs -o album_output/data.jl --logfile=album_output/output.log --loglevel=INFO
scrapy crawl songs_by_genre -o genre_output/data.jl --logfile=genre_output/output.log --loglevel=INFO
scrapy crawl movie_songs -o movie_output/data.jl --logfile=movie_output/output.log --loglevel=INFO
